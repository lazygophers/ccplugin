#!/usr/bin/env node

// 零依赖的 JSON Schema 子集校验器。
//
// 它只服务一个目的：证明 references/*.schema.json 与 ask-ui.mjs 里手写的校验
// 规则**对齐**（self-test 会拿同一批样例喂给两边，比对判定）。运行时的问题集
// 校验仍然走 ask-ui.mjs，因为那边报的是中文业务错误，Agent 照着一次就能改对。
//
// 支持的关键字止步于 schema 里真正用到的那些：$ref（仅 # 开头的本文档指针）、
// type、const、enum、pattern、minLength、maxLength、minimum、minItems、maxItems、
// items、properties、required、additionalProperties、oneOf、anyOf、allOf、
// if/then/else。format 只作注解，不校验。遇到没实现的关键字直接抛错，免得
// schema 加了新写法而校验悄悄放行。

const KNOWN_KEYWORDS = new Set([
  '$schema', '$id', '$ref', '$comment', '$defs', 'title', 'description', 'default', 'examples', 'format',
  'type', 'const', 'enum', 'pattern', 'minLength', 'maxLength', 'minimum', 'maximum',
  'minItems', 'maxItems', 'items', 'properties', 'required', 'additionalProperties',
  'oneOf', 'anyOf', 'allOf', 'not', 'if', 'then', 'else',
]);

function typeOf(value) {
  if (value === null) return 'null';
  if (Array.isArray(value)) return 'array';
  if (Number.isInteger(value)) return 'integer';
  return typeof value;
}

function matchesType(value, expected) {
  const actual = typeOf(value);
  if (expected === 'number') return actual === 'number' || actual === 'integer';
  if (expected === 'integer') return actual === 'integer';
  return actual === expected;
}

function deepEqual(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function resolveRef(root, ref) {
  if (!ref.startsWith('#/')) throw new Error(`unsupported $ref ${ref}（只支持本文档内的 #/ 指针）`);
  let node = root;
  for (const rawSegment of ref.slice(2).split('/')) {
    const segment = rawSegment.replace(/~1/g, '/').replace(/~0/g, '~');
    node = node?.[segment];
    if (node === undefined) throw new Error(`$ref ${ref} 指向不存在的节点`);
  }
  return node;
}

function validateNode(value, schema, { root, path, errors }) {
  if (schema === true) return;
  if (schema === false) {
    errors.push({ path, message: '此处不允许出现任何值' });
    return;
  }

  for (const keyword of Object.keys(schema)) {
    if (!KNOWN_KEYWORDS.has(keyword)) {
      throw new Error(`schema 用了本校验器没实现的关键字 ${keyword}（位置 ${path || '/'}）`);
    }
  }

  if (schema.$ref) {
    validateNode(value, resolveRef(root, schema.$ref), { root, path, errors });
    // $ref 与同级关键字并存时，2020-12 要求两者都生效。
  }

  if (schema.type !== undefined) {
    const expected = Array.isArray(schema.type) ? schema.type : [schema.type];
    if (!expected.some((candidate) => matchesType(value, candidate))) {
      errors.push({ path, message: `类型应为 ${expected.join(' 或 ')}，实际是 ${typeOf(value)}` });
      return;
    }
  }

  if (schema.const !== undefined && !deepEqual(value, schema.const)) {
    errors.push({ path, message: `值应为 ${JSON.stringify(schema.const)}` });
  }

  if (schema.enum !== undefined && !schema.enum.some((candidate) => deepEqual(value, candidate))) {
    errors.push({ path, message: `值应为 ${schema.enum.map((item) => JSON.stringify(item)).join(' / ')} 之一` });
  }

  if (typeof value === 'string') {
    if (schema.minLength !== undefined && [...value].length < schema.minLength) {
      errors.push({ path, message: `长度至少 ${schema.minLength}` });
    }
    if (schema.maxLength !== undefined && [...value].length > schema.maxLength) {
      errors.push({ path, message: `长度至多 ${schema.maxLength}` });
    }
    if (schema.pattern !== undefined && !new RegExp(schema.pattern).test(value)) {
      errors.push({ path, message: `不匹配 ${schema.pattern}` });
    }
  }

  if (typeof value === 'number') {
    if (schema.minimum !== undefined && value < schema.minimum) {
      errors.push({ path, message: `不得小于 ${schema.minimum}` });
    }
    if (schema.maximum !== undefined && value > schema.maximum) {
      errors.push({ path, message: `不得大于 ${schema.maximum}` });
    }
  }

  if (Array.isArray(value)) {
    if (schema.minItems !== undefined && value.length < schema.minItems) {
      errors.push({ path, message: `至少要有 ${schema.minItems} 项，实际 ${value.length} 项` });
    }
    if (schema.maxItems !== undefined && value.length > schema.maxItems) {
      errors.push({ path, message: `至多 ${schema.maxItems} 项，实际 ${value.length} 项` });
    }
    if (schema.items !== undefined) {
      value.forEach((item, index) => {
        validateNode(item, schema.items, { root, path: `${path}/${index}`, errors });
      });
    }
  }

  if (value && typeof value === 'object' && !Array.isArray(value)) {
    for (const key of schema.required || []) {
      if (!Object.hasOwn(value, key)) errors.push({ path, message: `缺少必填字段 ${key}` });
    }
    const declared = schema.properties || {};
    for (const [key, child] of Object.entries(declared)) {
      if (Object.hasOwn(value, key)) {
        validateNode(value[key], child, { root, path: `${path}/${key}`, errors });
      }
    }
    if (schema.additionalProperties === false) {
      for (const key of Object.keys(value)) {
        if (!Object.hasOwn(declared, key)) {
          errors.push({ path, message: `出现未定义的字段 ${key}` });
        }
      }
    } else if (schema.additionalProperties && typeof schema.additionalProperties === 'object') {
      for (const key of Object.keys(value)) {
        if (Object.hasOwn(declared, key)) continue;
        validateNode(value[key], schema.additionalProperties, { root, path: `${path}/${key}`, errors });
      }
    }
  }

  for (const branch of schema.allOf || []) {
    validateNode(value, branch, { root, path, errors });
  }

  if (schema.anyOf) {
    const passed = schema.anyOf.some((branch) => collect(value, branch, root, path).length === 0);
    if (!passed) errors.push({ path, message: '不满足 anyOf 里的任何一个分支' });
  }

  if (schema.oneOf) {
    const branchErrors = schema.oneOf.map((branch) => collect(value, branch, root, path));
    const matched = branchErrors.filter((list) => list.length === 0).length;
    if (matched === 0) {
      // 只报「最接近」的那个分支的错，否则四个分支的报错糊成一片没法读。
      const closest = branchErrors.reduce((best, list) => (list.length < best.length ? list : best));
      errors.push(...closest);
    } else if (matched > 1) {
      errors.push({ path, message: `同时命中 ${matched} 个互斥分支` });
    }
  }

  if (schema.not && collect(value, schema.not, root, path).length === 0) {
    errors.push({ path, message: '命中了被禁止的形状' });
  }

  if (schema.if !== undefined) {
    const branch = collect(value, schema.if, root, path).length === 0 ? schema.then : schema.else;
    if (branch !== undefined) validateNode(value, branch, { root, path, errors });
  }
}

function collect(value, schema, root, path) {
  const errors = [];
  validateNode(value, schema, { root, path, errors });
  return errors;
}

// 返回 { valid, errors }，errors 是 [{ path, message }]，path 是 JSON Pointer。
export function validateAgainstSchema(value, schema) {
  const errors = collect(value, schema, schema, '');
  return { valid: errors.length === 0, errors };
}

export function formatSchemaErrors(errors) {
  return errors.map(({ path, message }) => `${path || '/'}: ${message}`).join('\n');
}

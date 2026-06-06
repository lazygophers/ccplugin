# 真实项目案例

## FastHTML（规范官方示例）

```markdown
# FastHTML

> FastHTML is a python library which brings together Starlette, Uvicorn, HTMX, and fastcore's `FT` "FastTags" into a library for creating server-rendered hypermedia applications.

Important notes:

- Although parts of its API are inspired by FastAPI, it is _not_ compatible with FastAPI syntax and is not targeted at creating API services
- FastHTML is compatible with JS-native web components and any vanilla JS library, but not with React, Vue, or Svelte.

## Docs

- [FastHTML quick start](https://docs.fastht.ml/tutorials/quickstart_for_web_devs.html.md): A brief overview of many FastHTML features
- [HTMX reference](https://raw.githubusercontent.com/bigskysoftware/htmx/master/www/content/reference.md): Brief description of all HTMX attributes, CSS classes, headers, events, extensions, js lib methods, and config options

## Examples

- [Todo list application](https://github.com/AnswerDotAI/fasthtml/blob/main/examples/adv_app.py): Detailed walk-thru of a complete CRUD app in FastHTML showing idiomatic use of FastHTML and HTMX patterns.

## Optional

- [Starlette full documentation](https://gist.githubusercontent.com/jph00/809e4a4808d4510be0e3dc9565e9cbd3/raw/9b717589ca44cedc8aaf00b2b8cacef922964c0f/starlette-sml.md): A subset of the Starlette documentation useful for FastHTML development.
```

## 餐厅示例（规范提供）

```markdown
# Nate the Great's Grill

> Nate the Great's Grill is a popular destination off of Sesame Street that has been serving the community for over 20 years. We offer the best BBQ for a great price.

Here are our weekly hours:

- Monday - Friday: 9am - 9pm
- Saturday: 11am - 9pm
- Sunday: Closed

## Menus

- [Lunch Menu](https://host/lunch.html.md): Our lunch menu served from 11am to 4pm every day.
- [Dinner Menu](https://host/dinner.html.md): Our dinner menu served from 4pm to 9pm every day.

## Optional

- [Dessert Menu](https://host/dessert.md): Our dessert selection
```

## 最小合规示例

```markdown
# My Project
```

H1 标题是唯一必需部分。以上即为合规的 llms.txt。

## ccplugin 项目（本插件自身）

```markdown
# plugin-llms

> llms.txt 标准插件 - 通过 Agent 自动生成符合 llmstxt.org 规范的文件

## Docs

- [README](./README.md): 完整使用文档和安装指南
- [格式规范](./skills/llms-spec/references/format.md): llms.txt 文件格式完整规范
- [验证规则](./skills/llms-spec/references/validation.md): 验证规则和检查清单

## Examples

- [Agent 定义](./agents/llms-generator.md): llms.txt 生成 Agent 实现
- [真实案例](./skills/llms-spec/references/examples.md): 各项目 llms.txt 实例

## Optional

- [上下文变体](./skills/llms-spec/references/ctx-variants.md): llms-ctx 文件格式
- [工具集成](./skills/llms-spec/references/integrations.md): 工具库和框架插件
```

## 解析后的数据结构

```python
{
    'title': 'FastHTML',
    'summary': 'FastHTML is a python library which...',
    'info': 'Important notes:\n\n- Although parts...',
    'sections': {
        'Docs': [
            {'title': 'FastHTML quick start', 'url': 'https://...', 'desc': 'A brief overview...'},
        ],
        'Examples': [
            {'title': 'Todo list application', 'url': 'https://...', 'desc': 'Detailed walk-thru...'},
        ],
        'Optional': [
            {'title': 'Starlette full documentation', 'url': 'https://...', 'desc': 'A subset of...'},
        ]
    }
}
```

每个链接条目三个字段：`title`（必需）、`url`（必需）、`desc`（可选）。

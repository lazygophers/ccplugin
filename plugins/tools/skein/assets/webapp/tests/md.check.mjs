import assert from 'assert';
import { normalize, render, isPlaceholder } from '../src/new/lib/md.js';
// normalize 自动修复
assert.equal(normalize('##标题').trim(), '## 标题');
assert.equal(normalize('-项').trim(), '- 项');
assert.equal(normalize('1.项').trim(), '1. 项');
assert.equal(normalize('>引用').trim(), '> 引用');
assert.equal(normalize('- [x]完成').trim(), '- [x] 完成');
assert.equal(normalize('---').trim(), '---');            // 分隔线不动
assert.equal(normalize('**粗体**').trim(), '**粗体**');   // 粗体不动
assert.ok(normalize('```\ncode').endsWith('```'));        // 未闭合围栏补齐
assert.equal(normalize('```\n##不动\n```').split('\n')[1], '##不动'); // 围栏内原样
// render 产出
assert.ok(render('##标题').includes('<h2>标题</h2>'));
assert.ok(render('|a|b|\n|-|-|\n|1|2|').includes('<table>'));
console.log('md OK');

// 模板占位判定
const docEmpty = isPlaceholder;
assert.equal(docEmpty('# x — 调研收敛\n\n深度调研的收敛结论 + 依据/引用 (过程笔记存 research/):\n'), true);
assert.equal(docEmpty('# x\n\n说明:\n- 真内容\n'), false);
assert.equal(docEmpty(null), true);
console.log('docEmpty OK');


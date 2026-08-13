# Clean Code 调研综述（证据底稿）

> 一手语料：github.com/glen9527/Clean-Code-zh（clone 于 /tmp，调研后清理）。
> 本书 ch1-8 中英双语，ch9-17 英文原版（翻译未完成）。规则语言无关，证据引原文。
> 调研时间：2026-07-01。

## 一、ch17 坏味道与启发式 66 条全表（最高密度规则源）

```
COMMENTS
C1: Inappropriate Information        不恰当信息（变更历史/作者/SPR 号不进注释）
C2: Obsolete Comment                 过期注释（比没注释更糟）
C3: Redundant Comment                多余注释（i++; // increment i）
C4: Poorly Written Comment           写得烂的注释
C5: Commented-Out Code               注释掉的代码（删，源码控制会记）

ENVIRONMENT
E1: Build Requires More Than One Step    构建多步
E2: Tests Require More Than One Step     测试多步

FUNCTIONS
F1: Too Many Arguments           参数过多
F2: Output Arguments             输出参数
F3: Flag Arguments               flag 参数（布尔入参 = 函数做两件事）
F4: Dead Function                死函数

GENERAL (G1-G36)
G1: Multiple Languages in One Source File     单文件多语言
G2: Obvious Behavior Is Unimplemented         明显行为未实现
G3: Incorrect Behavior at the Boundaries      边界行为错
G4: Overridden Safeties                       关闭安全检查
G5: Duplication                               重复（DRY 违反）
G6: Code at Wrong Level of Abstraction        抽象层级错位
G7: Base Classes Depending on Their Derivatives  基类依赖派生
G8: Too Much Information                      信息过多
G9: Dead Code                                 死代码
G10: Vertical Separation                      垂直分隔（私有函数应近首调处）
G11: Inconsistency                            不一致
G12: Clutter                                  杂物
G13: Artificial Coupling                      人为耦合
G14: Feature Envy                             特性依恋（方法对别类数据更感兴趣）
G15: Selector Arguments                       选择器参数（枚举/布尔当分发器）
G16: Obscured Intent                          意图模糊
G17: Misplaced Responsibility                 责任错位
G18: Inappropriate Static                     不当 static
G19: Use Explanatory Variables                用解释性变量
G20: Function Names Should Say What They Do   函数名应表所为
G21: Understand the Algorithm                 理解算法（别靠凑）
G22: Make Logical Dependencies Physical       逻辑依赖转物理
G23: Prefer Polymorphism to If/Else/Switch    多态优于分支
G24: Follow Standard Conventions              遵循标准约定
G25: Replace Magic Numbers with Named Constants  魔法数→具名常量
G26: Be Precise                               精确（别蒙混）
G27: Structure over Convention                结构优于约定
G28: Encapsulate Conditionals                 封装条件
G29: Avoid Negative Conditionals              避免否定条件
G30: Functions Should Do One Thing            函数只做一件事
G31: Hidden Temporal Couplings                隐藏时序耦合
G32: Don't Be Arbitrary                       别武断
G33: Encapsulate Boundary Conditions          封装边界条件
G34: Functions Should Descend Only One Level of Abstraction  函数只降一层抽象
G35: Keep Configurable Data at High Levels    可配数据置高层
G36: Avoid Transitive Navigation             避免传递导航（火车失事）

JAVA
J1: Avoid Long Import Lists by Using Wildcards   通配符 import
J2: Don't Inherit Constants                      别继承常量
J3: Constants versus Enums                       常量 vs 枚举

NAMES
N1: Choose Descriptive Names                    选描述性名
N2: Choose Names at the Appropriate Level of Abstraction  名配抽象层级
N3: Use Standard Nomenclature Where Possible    用标准术语
N4: Unambiguous Names                           不含糊的名
N5: Use Long Names for Long Scopes              长作用域配长名
N6: Avoid Encodings                             避免编码
N7: Names Should Describe Side-Effects          名描述副作用

TESTS
T1: Insufficient Tests                测试不充分
T2: Use a Coverage Tool!              用覆盖率工具
T3: Don't Skip Trivial Tests          别跳过平凡测试
T4: An Ignored Test Is a Question about an Ambiguity  忽略测试=对歧义提问
T5: Test Boundary Conditions          测边界条件
T6: Exhaustively Test Near Bugs       bug 附近穷尽测
T7: Patterns of Failure Are Revealing 失败模式揭示问题
T8: Test Coverage Patterns Can Be Revealing  覆盖率模式揭示遗漏
T9: Tests Should Be Fast              测试要快
```

## 二、ch12 Kent Beck 简单设计四原则（原文，按重要性递减）

> According to Kent, a design is "simple" if it follows these rules:
> - Runs all the tests
> - Contains no duplication
> - Expresses the intent of the programmer
> - Minimizes the number of classes and methods

## 三、ch1.3.5 名家整洁代码定义（原文）

**Bjarne Stroustrup**（C++ 发明者）：
> I like my code to be elegant and efficient. The logic should be straightforward to make it hard for bugs to hide, the dependencies minimal to ease maintenance, error handling complete according to an articulated strategy, and performance close to optimal so as not to tempt people to make the code messy with unprincipled optimizations. **Clean code does one thing well.**

核心：优雅 + 效率（两次提及）+ 最小依赖 + 完整错误处理 + 近最优性能。Uncle Bob 注：浪费的运算周期「不雅观」；坏代码「引诱」越改越烂。

## 四、章节级规则大纲（已提炼入 SKILL.md「规则体系」节）

| 章 | 主题 | SKILL.md 对应节 |
|----|------|----------------|
| ch1 | 整洁代码（哲学） | 核心哲学 |
| ch2 | 有意义的命名 | 命名 |
| ch3 | 函数 | 函数 |
| ch4 | 注释 | 注释 |
| ch5 | 格式 | 格式 |
| ch6 | 对象和数据结构 | 数据/对象 |
| ch7 | 错误处理 | 错误处理 |
| ch8 | 边界 | 边界 |
| ch9 | 单元测试 | 测试 |
| ch10 | 类 | 类 |
| ch11 | 系统 | 系统 |
| ch12 | 迭进（涌现设计） | 简单设计四原则 |
| ch13 | 并发编程 | 并发 |
| ch14 | 逐步改进（案例） | 诚实边界（案例不照搬） |
| ch15 | JUnit 内幕（案例） | 同上 |
| ch16 | 重构 SerialDate（案例） | 同上 |
| ch17 | 味道与启发 | 66 条总表 |
| 附录 A | 并发编程 II | 并发 |

## 五、信息缺口与诚实标注

- ch9-17 为英文原版（翻译未完成）；规则措辞以英文原文为准，中文为本 skill 译者注。
- ch14/15/16 为长篇逐步重构案例，本 skill 不抄其过程，仅引章节号供查阅。
- 附录 A（并发 II）同 ch13 并发主题，合并入「并发」节。
- 当代语言原生支持（Optional / Result / async / 所有权）原书未覆盖，已在「诚实边界」标注。

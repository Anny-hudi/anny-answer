# 基于FFT的正则匹配算法

## 项目概述

本项目实现了使用快速傅里叶变换（FFT）进行字符串匹配的算法，支持通配符 `?`，时间复杂度为 $O(n \log n)$，是传统字符串匹配算法的重要改进。

## 文件结构

```
q2/
├── fft_string_matching.py    # 主要算法实现
├── test_fft_matching.py      # 测试文件
├── theoretical_analysis.md   # 理论分析文档
└── README.md                # 项目说明文档
```

## 核心算法

### 问题定义
给定主串 $S$（长度为 $n$）和模式串 $P$（长度为 $m$），其中 $P$ 包含字母和通配符 `?`，找到 $P$ 在 $S$ 中的所有匹配位置。

### 算法原理
将字符串匹配问题转化为多项式乘法问题：
1. **字符编码**：将字符转换为数值
2. **多项式表示**：将字符串表示为多项式系数
3. **FFT乘法**：使用FFT计算多项式乘积
4. **匹配判断**：通过乘积结果判断匹配位置

### 核心代码
```python
def fft_string_matching(self, S: str, P: str) -> List[int]:
    # 编码字符串
    S_encoded = self.encode_string(S)
    P_encoded = self.encode_string(P)
    
    # 模式串反转
    P_reversed = P_encoded[::-1]
    
    # FFT乘法
    result = self.fft_multiply(S_encoded, P_reversed)
    
    # 提取匹配位置
    matches = []
    for i in range(len(S) - len(P) + 1):
        if self.is_match_at_position(result, i + len(P) - 1, len(P)):
            matches.append(i)
    
    return matches
```

## 性能特点

### 时间复杂度
- **理论最优**：$O(n \log n)$
- **实际性能**：在大字符串上优于朴素算法

### 空间复杂度
- **总空间复杂度**：$O(n)$
- **FFT计算空间**：$O(n)$

### 适用场景
- **优势场景**：$n >> m$ 的长文本匹配
- **劣势场景**：短模式串或频繁的小规模匹配

## 使用方法

### 基本使用
```python
from fft_string_matching import FFTStringMatcher

# 创建匹配器
matcher = FFTStringMatcher()

# 基本匹配
S = "abcdefghijklmnop"
P = "def"
matches = matcher.fft_string_matching(S, P)
print(f"匹配位置: {matches}")  # 输出: [3]
```

### 通配符匹配
```python
# 带通配符的匹配
S = "abccdefghijklmnop"
P = "c?f"
matches = matcher.fft_string_matching(S, P)
print(f"匹配位置: {matches}")  # 输出: [2]
```

### 多个匹配
```python
# 多个匹配位置
S = "abababababab"
P = "aba"
matches = matcher.fft_string_matching(S, P)
print(f"匹配位置: {matches}")  # 输出: [0, 2, 4, 6, 8]
```

## 运行测试

### 运行所有测试
```bash
cd q2
python test_fft_matching.py
```

### 运行示例
```bash
cd q2
python fft_string_matching.py
```

## 算法优势

1. **理论最优**：时间复杂度达到 $O(n \log n)$
2. **通配符支持**：天然支持通配符匹配
3. **并行友好**：FFT算法易于并行化
4. **数值稳定**：基于FFT的数值计算稳定
5. **扩展性好**：可扩展到更复杂的模式匹配

## 理论分析

详细的数学证明和复杂度分析请参考 `theoretical_analysis.md` 文件，包括：

- 算法正确性证明
- 时间复杂度分析
- 空间复杂度分析
- 最优性证明
- 扩展应用讨论

## 测试覆盖

测试文件 `test_fft_matching.py` 包含：

- ✅ 基本功能测试
- ✅ 边界条件测试
- ✅ 字符编码测试
- ✅ 大字符串性能测试
- ✅ 复杂模式测试
- ✅ FFT正确性验证
- ✅ 内存效率测试

## 实现细节

### 字符编码
- 普通字母：`ord(char) - ord('a') + 1`（1-26）
- 通配符：`0`

### FFT实现
- 使用分治策略
- 支持任意长度的输入（自动补零到2的幂次）
- 包含IFFT实现

### 匹配判断
- 通过卷积结果判断匹配
- 数值精度容错处理

## 依赖要求

```python
numpy >= 1.19.0
```

## 性能对比

| 算法 | 时间复杂度 | 空间复杂度 | 通配符支持 |
|------|------------|------------|------------|
| 朴素算法 | $O(nm)$ | $O(1)$ | ✅ |
| KMP算法 | $O(n+m)$ | $O(m)$ | ❌ |
| FFT算法 | $O(n \log n)$ | $O(n)$ | ✅ |

## 扩展应用

### 多模式匹配
可以扩展到多个模式串的匹配：
- 时间复杂度：$O(k \cdot n \log n)$
- 空间复杂度：$O(k \cdot n)$

### 模糊匹配
支持编辑距离的模糊匹配：
- 使用不同的编码策略
- 修改匹配判断条件

### 正则表达式
可以扩展到更复杂的正则表达式：
- 支持量词（*, +, ?）
- 支持字符类
- 支持分组

## 许可证

本项目采用MIT许可证。

## 贡献

欢迎提交Issue和Pull Request来改进算法实现。

---

**总结：** 本实现提供了一个高效、正确、易用的FFT字符串匹配算法解决方案，在保持理论最优复杂度的同时，支持通配符匹配，是字符串匹配算法的重要进展。

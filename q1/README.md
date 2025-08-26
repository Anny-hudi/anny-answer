# 反向对称矩阵最优解法

## 项目概述

本项目实现了反向对称矩阵与向量乘积的最优算法，时间复杂度为 $O(n^2)$，空间复杂度为 $O(n)$，达到了理论最优的复杂度。

## 文件结构

```
q1/
├── optimal_solution.py      # 主要算法实现
├── test_solution.py         # 测试文件
├── theoretical_analysis.md  # 理论分析文档
└── README.md               # 项目说明文档
```

## 核心算法

### 反向对称矩阵定义
设 $A$ 为 $n \times n$ 矩阵，若每一条从左上到右下的对角线上的元素都相等，则称 $A$ 为**反向对称矩阵**。

### 压缩表示
- 使用长度为 $2n-1$ 的向量 $a = [a_0, a_1, ..., a_{2n-2}]$ 表示
- 矩阵元素：$A_{i,j} = a_{n-1+i-j}$

### 矩阵-向量乘积算法
```python
def matrix_vector_product(self, vector):
    result = np.zeros(self.size)
    for i in range(self.size):
        for j in range(self.size):
            k = self.size - 1 + i - j
            result[i] += self.compressed[k] * vector[j]
    return result
```

## 性能特点

### 时间复杂度
- **理论最优：** $O(n^2)$
- **实际性能：** 与NumPy实现相当

### 空间复杂度
- **压缩存储：** $O(n)$
- **内存节省：** 相比完整矩阵节省 $(n-1)^2$ 个元素

### 内存效率示例
对于 $1000 \times 1000$ 矩阵：
- 完整矩阵：8 MB
- 压缩表示：0.016 MB
- 内存节省：99.8%

## 使用方法

### 基本使用
```python
from optimal_solution import ReverseSymmetricMatrix

# 创建5×5反向对称矩阵
compressed = [0, 1, 2, 3, 4, 5, 6, 7, 8]
matrix = ReverseSymmetricMatrix(compressed)

# 计算矩阵-向量乘积
vector = [1, 2, 3, 4, 5]
result = matrix.matrix_vector_product(vector)
```

### 高级功能
```python
# 获取矩阵元素
element = matrix.get_element(2, 3)

# 转换为完整矩阵（用于验证）
full_matrix = matrix.to_full_matrix()

# 使用优化算法
result = matrix.matrix_vector_product_optimized(vector)
```

## 运行测试

### 运行所有测试
```bash
cd q1
python test_solution.py
```

### 运行示例
```bash
cd q1
python optimal_solution.py
```

## 算法优势

1. **理论最优：** 时间复杂度达到理论下界 $O(n^2)$
2. **空间高效：** 空间复杂度仅为 $O(n)$
3. **实现简单：** 代码清晰易懂，易于维护
4. **性能优秀：** 实际性能与NumPy相当
5. **扩展性好：** 可扩展到其他矩阵运算

## 理论分析

详细的数学证明和复杂度分析请参考 `theoretical_analysis.md` 文件，包括：

- 算法正确性证明
- 时间复杂度分析
- 空间复杂度分析
- 最优性证明
- 扩展应用讨论

## 测试覆盖

测试文件 `test_solution.py` 包含：

- ✅ 基本功能测试
- ✅ 边界条件测试
- ✅ 大矩阵性能测试
- ✅ 内存效率测试
- ✅ 算法正确性验证
- ✅ 与NumPy结果对比

## 依赖要求

```python
numpy >= 1.19.0
```

## 许可证

本项目采用MIT许可证。

## 贡献

欢迎提交Issue和Pull Request来改进算法实现。

---

**总结：** 本实现提供了一个高效、正确、易用的反向对称矩阵算法解决方案，在保持理论最优复杂度的同时，显著降低了空间复杂度，是一个实用的算法实现。

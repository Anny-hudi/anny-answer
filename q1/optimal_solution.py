import numpy as np
from typing import List, Union
import time


class ReverseSymmetricMatrix:
    """
    反向对称矩阵类
    
    使用压缩表示存储反向对称矩阵，只需要2n-1个元素而不是n²个元素。
    """
    
    def __init__(self, compressed_vector: List[Union[int, float]]):
        """
        初始化反向对称矩阵
        
        Args:
            compressed_vector: 压缩向量，长度为2n-1
        """
        self.compressed = np.array(compressed_vector, dtype=float)
        self.size = (len(compressed_vector) + 1) // 2  # n = (2n-1 + 1) // 2
        
        if len(compressed_vector) != 2 * self.size - 1:
            raise ValueError(f"压缩向量长度必须为2n-1，当前长度为{len(compressed_vector)}")
    
    def get_element(self, i: int, j: int) -> float:
        """
        获取矩阵元素A[i,j]
        
        Args:
            i: 行索引 (0 <= i < n)
            j: 列索引 (0 <= j < n)
            
        Returns:
            矩阵元素值
        """
        if not (0 <= i < self.size and 0 <= j < self.size):
            raise IndexError(f"索引({i},{j})超出矩阵范围[0,{self.size})")
        
        k = self.size - 1 + i - j
        return self.compressed[k]
    
    def to_full_matrix(self) -> np.ndarray:
        """
        转换为完整的n×n矩阵（用于验证）
        
        Returns:
            完整的矩阵
        """
        matrix = np.zeros((self.size, self.size))
        for i in range(self.size):
            for j in range(self.size):
                matrix[i, j] = self.get_element(i, j)
        return matrix
    
    def matrix_vector_product(self, vector: List[Union[int, float]]) -> np.ndarray:
        """
        计算矩阵-向量乘积 A·v
        
        最优算法实现，时间复杂度O(n²)，空间复杂度O(n)
        
        Args:
            vector: 输入向量，长度为n
            
        Returns:
            结果向量 A·v
        """
        if len(vector) != self.size:
            raise ValueError(f"向量长度必须为{self.size}，当前长度为{len(vector)}")
        
        v = np.array(vector, dtype=float)
        result = np.zeros(self.size)
        
        # 最优算法：直接计算每个结果元素
        for i in range(self.size):
            for j in range(self.size):
                k = self.size - 1 + i - j
                result[i] += self.compressed[k] * v[j]
        
        return result


def benchmark_algorithms(n: int, num_trials: int = 100):
    """
    性能基准测试
    
    Args:
        n: 矩阵大小
        num_trials: 测试次数
    """
    print(f"=== 性能基准测试 (n={n}) ===")
    
    # 生成测试数据
    compressed = np.random.rand(2*n-1)
    vector = np.random.rand(n)
    
    # 创建矩阵对象
    matrix = ReverseSymmetricMatrix(compressed.tolist())
    
    # 测试最优算法
    start_time = time.time()
    for _ in range(num_trials):
        result1 = matrix.matrix_vector_product(vector.tolist())
    algorithm_time = time.time() - start_time
    
    # 测试NumPy实现（作为参考）
    full_matrix = matrix.to_full_matrix()
    start_time = time.time()
    for _ in range(num_trials):
        result2 = full_matrix @ vector
    numpy_time = time.time() - start_time
    
    # 验证结果一致性
    assert np.allclose(result1, result2), "自定义算法和NumPy结果不一致"
    
    print(f"最优算法时间:      {algorithm_time:.6f}s")
    print(f"NumPy实现时间:     {numpy_time:.6f}s")
    print(f"相对NumPy性能:     {numpy_time/algorithm_time:.2f}x")
    print()


def example_usage():
    """
    使用示例
    """
    print("=== 反向对称矩阵使用示例 ===")
    
    # 创建5×5反向对称矩阵的压缩表示
    # 对应矩阵：
    # [4, 3, 2, 1, 0]
    # [5, 4, 3, 2, 1]
    # [6, 5, 4, 3, 2]
    # [7, 6, 5, 4, 3]
    # [8, 7, 6, 5, 4]
    compressed = [0, 1, 2, 3, 4, 5, 6, 7, 8]  # 长度为2*5-1=9
    
    # 创建矩阵对象
    matrix = ReverseSymmetricMatrix(compressed)
    
    # 显示完整矩阵
    print("完整矩阵:")
    print(matrix.to_full_matrix())
    print()
    
    # 测试向量
    vector = [1, 2, 3, 4, 5]
    print(f"输入向量: {vector}")
    
    # 计算矩阵-向量乘积
    result = matrix.matrix_vector_product(vector)
    print(f"结果向量: {result}")
    
    # 验证结果
    expected = matrix.to_full_matrix() @ np.array(vector)
    print(f"期望结果: {expected}")
    print(f"结果正确: {np.allclose(result, expected)}")
    print()


def complexity_analysis():
    """
    复杂度分析演示
    """
    print("=== 复杂度分析演示 ===")
    
    sizes = [10, 50, 100, 200, 500]
    times = []
    
    for n in sizes:
        compressed = np.random.rand(2*n-1)
        vector = np.random.rand(n)
        matrix = ReverseSymmetricMatrix(compressed.tolist())
        
        # 预热
        for _ in range(10):
            matrix.matrix_vector_product(vector.tolist())
        
        # 计时
        start_time = time.time()
        for _ in range(100):
            matrix.matrix_vector_product(vector.tolist())
        elapsed = time.time() - start_time
        
        times.append(elapsed)
        print(f"n={n:3d}: {elapsed:.6f}s")
    
    # 验证O(n²)复杂度
    print("\n复杂度验证:")
    for i in range(1, len(sizes)):
        ratio = times[i] / times[i-1]
        size_ratio = (sizes[i] / sizes[i-1]) ** 2
        print(f"n={sizes[i-1]}→{sizes[i]}: 时间比={ratio:.2f}, 理论比={size_ratio:.2f}")


if __name__ == "__main__":
    # 运行示例
    example_usage()
    
    # 运行基准测试
    for n in [10, 50, 100]:
        benchmark_algorithms(n, num_trials=100)
    
    # 复杂度分析
    complexity_analysis()

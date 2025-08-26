"""
反向对称矩阵算法测试文件

该文件包含全面的测试用例，验证算法的正确性、性能和边界条件。
"""

import numpy as np
import time
import sys
import os

# 添加父目录到路径以导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from optimal_solution import ReverseSymmetricMatrix


def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试基本功能 ===")
    
    # 测试用例1：3×3矩阵
    compressed = [1, 2, 3, 4, 5]  # 长度为2*3-1=5
    matrix = ReverseSymmetricMatrix(compressed)
    
    expected_matrix = np.array([
        [3, 2, 1],
        [4, 3, 2],
        [5, 4, 3]
    ])
    
    actual_matrix = matrix.to_full_matrix()
    assert np.array_equal(actual_matrix, expected_matrix), f"矩阵不匹配\n期望:\n{expected_matrix}\n实际:\n{actual_matrix}"
    print("✓ 3×3矩阵测试通过")
    
    # 测试矩阵-向量乘积
    vector = [1, 2, 3]
    result = matrix.matrix_vector_product(vector)
    expected = expected_matrix @ np.array(vector)
    assert np.allclose(result, expected), f"乘积结果不匹配\n期望: {expected}\n实际: {result}"
    print("✓ 矩阵-向量乘积测试通过")


def test_edge_cases():
    """测试边界条件"""
    print("\n=== 测试边界条件 ===")
    
    # 测试1×1矩阵
    compressed = [42]
    matrix = ReverseSymmetricMatrix(compressed)
    assert matrix.size == 1
    assert matrix.get_element(0, 0) == 42
    result = matrix.matrix_vector_product([5])
    assert result[0] == 210  # 42 * 5
    print("✓ 1×1矩阵测试通过")
    
    # 测试2×2矩阵
    compressed = [1, 2, 3]
    matrix = ReverseSymmetricMatrix(compressed)
    expected = np.array([[2, 1], [3, 2]])
    actual = matrix.to_full_matrix()
    assert np.array_equal(actual, expected)
    print("✓ 2×2矩阵测试通过")
    
    # 测试索引边界
    try:
        matrix.get_element(2, 0)  # 超出范围
        assert False, "应该抛出IndexError"
    except IndexError:
        print("✓ 索引边界检查通过")


def test_large_matrices():
    """测试大矩阵"""
    print("\n=== 测试大矩阵 ===")
    
    sizes = [10, 50, 100]
    for n in sizes:
        # 生成随机压缩向量
        compressed = np.random.rand(2*n-1)
        vector = np.random.rand(n)
        
        matrix = ReverseSymmetricMatrix(compressed.tolist())
        
        # 测试两种算法的一致性
        result1 = matrix.matrix_vector_product(vector.tolist())
        result2 = matrix.matrix_vector_product_optimized(vector.tolist())
        
        assert np.allclose(result1, result2), f"n={n}: 两种算法结果不一致"
        
        # 与NumPy结果比较
        full_matrix = matrix.to_full_matrix()
        expected = full_matrix @ vector
        assert np.allclose(result1, expected), f"n={n}: 与NumPy结果不一致"
        
        print(f"✓ {n}×{n}矩阵测试通过")


def test_performance():
    """性能测试"""
    print("\n=== 性能测试 ===")
    
    sizes = [100, 500, 1000]
    for n in sizes:
        compressed = np.random.rand(2*n-1)
        vector = np.random.rand(n)
        matrix = ReverseSymmetricMatrix(compressed.tolist())
        
        # 预热
        for _ in range(10):
            matrix.matrix_vector_product(vector.tolist())
        
        # 测试基本算法
        start_time = time.time()
        for _ in range(100):
            matrix.matrix_vector_product(vector.tolist())
        basic_time = time.time() - start_time
        
        # 测试优化算法
        start_time = time.time()
        for _ in range(100):
            matrix.matrix_vector_product_optimized(vector.tolist())
        optimized_time = time.time() - start_time
        
        # 测试NumPy
        full_matrix = matrix.to_full_matrix()
        start_time = time.time()
        for _ in range(100):
            full_matrix @ vector
        numpy_time = time.time() - start_time
        
        print(f"n={n:4d}: 基本={basic_time:.4f}s, 优化={optimized_time:.4f}s, NumPy={numpy_time:.4f}s")
        print(f"        优化加速比: {basic_time/optimized_time:.2f}x, 相对NumPy: {numpy_time/optimized_time:.2f}x")


def test_memory_efficiency():
    """内存效率测试"""
    print("\n=== 内存效率测试 ===")
    
    n = 1000
    compressed = np.random.rand(2*n-1)
    vector = np.random.rand(n)
    
    # 压缩表示的内存使用
    compressed_size = compressed.nbytes
    full_matrix_size = n * n * 8  # 假设double类型
    
    memory_saving = (full_matrix_size - compressed_size) / full_matrix_size * 100
    
    print(f"矩阵大小: {n}×{n}")
    print(f"完整矩阵内存: {full_matrix_size / 1024 / 1024:.2f} MB")
    print(f"压缩表示内存: {compressed_size / 1024 / 1024:.2f} MB")
    print(f"内存节省: {memory_saving:.1f}%")


def test_algorithm_correctness():
    """算法正确性验证"""
    print("\n=== 算法正确性验证 ===")
    
    # 使用已知的简单矩阵进行验证
    compressed = [0, 1, 2, 3, 4, 5, 6, 7, 8]  # 5×5矩阵
    matrix = ReverseSymmetricMatrix(compressed)
    
    # 手动计算期望结果
    full_matrix = matrix.to_full_matrix()
    vector = [1, 2, 3, 4, 5]
    
    # 手动计算第一行
    expected_row0 = (4*1 + 3*2 + 2*3 + 1*4 + 0*5)  # 40
    expected_row1 = (5*1 + 4*2 + 3*3 + 2*4 + 1*5)  # 35
    expected_row2 = (6*1 + 5*2 + 4*3 + 3*4 + 2*5)  # 30
    expected_row3 = (7*1 + 6*2 + 5*3 + 4*4 + 3*5)  # 25
    expected_row4 = (8*1 + 7*2 + 6*3 + 5*4 + 4*5)  # 20
    
    expected = np.array([expected_row0, expected_row1, expected_row2, expected_row3, expected_row4])
    
    result = matrix.matrix_vector_product(vector)
    assert np.allclose(result, expected), f"手动计算结果不匹配\n期望: {expected}\n实际: {result}"
    
    print("✓ 手动计算验证通过")


def run_all_tests():
    """运行所有测试"""
    print("开始运行反向对称矩阵算法测试...\n")
    
    try:
        test_basic_functionality()
        test_edge_cases()
        test_large_matrices()
        test_performance()
        test_memory_efficiency()
        test_algorithm_correctness()
        
        print("\n🎉 所有测试通过！")
        print("算法实现正确，性能良好。")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

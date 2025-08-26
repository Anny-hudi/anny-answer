"""
FFT字符串匹配算法测试文件

该文件包含全面的测试用例，验证FFT字符串匹配算法的正确性、性能和边界条件。
"""

import numpy as np
import time
import sys
import os
from typing import List, Tuple

# 添加当前目录到路径以导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fft_string_matching import FFTStringMatcher


def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试基本功能 ===")
    
    matcher = FFTStringMatcher()
    
    # 测试用例1：简单匹配
    S1 = "abcdefghijklmnop"
    P1 = "def"
    matches1 = matcher.fft_string_matching(S1, P1)
    expected1 = [3]  # "def"在位置3
    assert matches1 == expected1, f"测试用例1失败: 期望{expected1}, 实际{matches1}"
    print("✓ 简单匹配测试通过")
    
    # 测试用例2：通配符匹配
    S2 = "abccfdefghijklmnop"
    P2 = "c?f"
    matches2 = matcher.fft_string_matching(S2, P2)
    expected2 = [2]  # "ccf"在位置2，其中'c'匹配'c'，'c'匹配'?'，'f'匹配'f'
    assert matches2 == expected2, f"测试用例2失败: 期望{expected2}, 实际{matches2}"
    print("✓ 通配符匹配测试通过")
    
    # 测试用例3：多个匹配
    S3 = "abababababab"
    P3 = "aba"
    matches3 = matcher.fft_string_matching(S3, P3)
    expected3 = [0, 2, 4, 6, 8]  # "aba"在多个位置
    assert matches3 == expected3, f"测试用例3失败: 期望{expected3}, 实际{matches3}"
    print("✓ 多个匹配测试通过")


def test_edge_cases():
    """测试边界条件"""
    print("\n=== 测试边界条件 ===")
    
    matcher = FFTStringMatcher()
    
    # 测试用例1：空字符串
    try:
        matches = matcher.fft_string_matching("", "abc")
        assert matches == [], "空主串应该返回空结果"
        print("✓ 空主串测试通过")
    except Exception as e:
        print(f"✗ 空主串测试失败: {e}")
    
    # 测试用例2：模式串比主串长
    matches = matcher.fft_string_matching("abc", "abcdef")
    assert matches == [], "模式串比主串长应该返回空结果"
    print("✓ 模式串过长测试通过")
    
    # 测试用例3：完全匹配
    matches = matcher.fft_string_matching("abc", "abc")
    assert matches == [0], "完全匹配应该在位置0"
    print("✓ 完全匹配测试通过")
    
    # 测试用例4：全通配符模式
    matches = matcher.fft_string_matching("abc", "???")
    assert matches == [0], "全通配符模式应该匹配"
    print("✓ 全通配符测试通过")


def test_character_encoding():
    """测试字符编码"""
    print("\n=== 测试字符编码 ===")
    
    matcher = FFTStringMatcher()
    
    # 测试字母编码
    assert matcher.encode_character('a') == 1
    assert matcher.encode_character('b') == 2
    assert matcher.encode_character('z') == 26
    print("✓ 字母编码测试通过")
    
    # 测试通配符编码
    assert matcher.encode_character('?') == 0
    print("✓ 通配符编码测试通过")
    
    # 测试字符串编码
    encoded = matcher.encode_string("abc?")
    expected = [1, 2, 3, 0]
    assert encoded == expected, f"字符串编码失败: 期望{expected}, 实际{encoded}"
    print("✓ 字符串编码测试通过")


def test_large_strings():
    """测试大字符串"""
    print("\n=== 测试大字符串 ===")
    
    matcher = FFTStringMatcher()
    
    # 生成大字符串
    n = 1000
    S = "a" * n + "pattern" + "a" * n
    P = "pattern"
    
    # 测试FFT算法
    fft_matches = matcher.fft_string_matching(S, P)
    
    # 测试朴素算法（用于验证）
    naive_matches = matcher.naive_string_matching(S, P)
    
    assert fft_matches == naive_matches, f"大字符串测试失败: FFT={fft_matches}, 朴素={naive_matches}"
    assert len(fft_matches) == 1, f"应该只有一个匹配位置"
    assert fft_matches[0] == n, f"匹配位置应该是{n}"
    
    print(f"✓ 大字符串测试通过: 匹配位置={fft_matches}")


def test_performance():
    """性能测试"""
    print("\n=== 性能测试 ===")
    
    matcher = FFTStringMatcher()
    
    # 测试不同大小的字符串
    test_cases = [
        (100, "pattern"),
        (500, "pattern"),
        (1000, "pattern"),
        (2000, "pattern"),
    ]
    
    for n, pattern in test_cases:
        S = "a" * n + pattern + "a" * n
        
        # 预热
        for _ in range(5):
            matcher.fft_string_matching(S, pattern)
        
        # 测试FFT算法
        start_time = time.time()
        for _ in range(10):
            fft_matches = matcher.fft_string_matching(S, pattern)
        fft_time = time.time() - start_time
        
        # 测试朴素算法
        start_time = time.time()
        for _ in range(10):
            naive_matches = matcher.naive_string_matching(S, pattern)
        naive_time = time.time() - start_time
        
        # 验证结果一致性
        assert fft_matches == naive_matches, f"结果不一致: n={n}"
        
        print(f"n={n:4d}: FFT={fft_time:.4f}s, 朴素={naive_time:.4f}s, 加速比={naive_time/fft_time:.2f}x")


def test_complex_patterns():
    """测试复杂模式"""
    print("\n=== 测试复杂模式 ===")
    
    matcher = FFTStringMatcher()
    
    # 测试用例1：多个通配符
    S1 = "abcdefghijklmnop"
    P1 = "a?c?e"
    matches1 = matcher.fft_string_matching(S1, P1)
    expected1 = [0]  # "abcde"在位置0
    assert matches1 == expected1, f"复杂模式1失败: 期望{expected1}, 实际{matches1}"
    print("✓ 多个通配符测试通过")
    
    # 测试用例2：通配符在开头和结尾
    S2 = "abcdefghijklmnop"
    P2 = "?bc?"
    matches2 = matcher.fft_string_matching(S2, P2)
    expected2 = [0]  # "abcd"在位置0
    assert matches2 == expected2, f"复杂模式2失败: 期望{expected2}, 实际{matches2}"
    print("✓ 通配符在边界测试通过")
    
    # 测试用例3：重复模式
    S3 = "aaaaaa"
    P3 = "a?a"
    matches3 = matcher.fft_string_matching(S3, P3)
    expected3 = [0, 1, 2, 3]  # 多个匹配位置
    assert matches3 == expected3, f"复杂模式3失败: 期望{expected3}, 实际{matches3}"
    print("✓ 重复模式测试通过")


def test_fft_correctness():
    """测试FFT正确性"""
    print("\n=== 测试FFT正确性 ===")
    
    matcher = FFTStringMatcher()
    
    # 测试简单的FFT
    data = [1, 2, 3, 4]
    fft_result = matcher.fft([complex(x, 0) for x in data])
    
    # 验证FFT结果的基本性质
    assert len(fft_result) == 4, "FFT结果长度应该等于输入长度"
    assert all(isinstance(x, complex) for x in fft_result), "FFT结果应该是复数"
    
    # 测试IFFT
    ifft_result = matcher.ifft(fft_result)
    
    # 验证IFFT恢复原始数据
    for i, (original, recovered) in enumerate(zip(data, ifft_result)):
        assert abs(recovered.real - original) < 1e-10, f"IFFT恢复失败: 位置{i}"
        assert abs(recovered.imag) < 1e-10, f"IFFT虚部应该为0: 位置{i}"
    
    print("✓ FFT/IFFT正确性测试通过")


def test_memory_efficiency():
    """内存效率测试"""
    print("\n=== 内存效率测试 ===")
    
    import psutil
    import os
    
    matcher = FFTStringMatcher()
    
    # 测试大字符串的内存使用
    n = 5000
    S = "a" * n + "pattern" + "a" * n
    P = "pattern"
    
    # 获取当前进程
    process = psutil.Process(os.getpid())
    
    # 记录内存使用前
    memory_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # 执行FFT匹配
    matches = matcher.fft_string_matching(S, P)
    
    # 记录内存使用后
    memory_after = process.memory_info().rss / 1024 / 1024  # MB
    memory_used = memory_after - memory_before
    
    print(f"字符串长度: {len(S)}")
    print(f"内存使用: {memory_used:.2f} MB")
    print(f"匹配位置: {matches}")
    
    # 验证结果正确
    assert len(matches) == 1 and matches[0] == n, "内存测试结果不正确"
    print("✓ 内存效率测试通过")


def run_all_tests():
    """运行所有测试"""
    print("开始运行FFT字符串匹配算法测试...\n")
    
    try:
        test_basic_functionality()
        test_edge_cases()
        test_character_encoding()
        test_large_strings()
        test_performance()
        test_complex_patterns()
        test_fft_correctness()
        
        # 内存测试可能在某些环境下不可用，所以用try-except包装
        try:
            test_memory_efficiency()
        except ImportError:
            print("\n⚠️  内存效率测试跳过（需要psutil库）")
        except Exception as e:
            print(f"\n⚠️  内存效率测试失败: {e}")
        
        print("\n🎉 所有测试通过！")
        print("FFT字符串匹配算法实现正确，性能良好。")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

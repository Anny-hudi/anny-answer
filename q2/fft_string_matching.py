"""
基于FFT的正则匹配算法实现

该模块实现了使用快速傅里叶变换（FFT）进行字符串匹配的算法，
支持通配符?，时间复杂度O(n log n)。
"""

import numpy as np
import cmath
from typing import List, Tuple
import time


class FFTStringMatcher:
    """
    基于FFT的字符串匹配器
    
    使用快速傅里叶变换实现字符串匹配，支持通配符。
    """
    
    def __init__(self):
        """初始化FFT字符串匹配器"""
        pass
    
    def encode_character(self, char: str) -> int:
        """
        字符编码函数
        
        Args:
            char: 要编码的字符
            
        Returns:
            编码后的数值
        """
        if char == '?':
            return 0  # 通配符编码为0
        else:
            return ord(char) - ord('a') + 1  # 字母编码为1-26
    
    def encode_string(self, s: str) -> List[int]:
        """
        字符串编码函数
        
        Args:
            s: 要编码的字符串
            
        Returns:
            编码后的数值列表
        """
        return [self.encode_character(c) for c in s]
    
    def fft(self, data: List[complex]) -> List[complex]:
        """
        快速傅里叶变换
        
        Args:
            data: 输入数据（复数列表）
            
        Returns:
            FFT结果
        """
        n = len(data)
        if n == 1:
            return data
        
        # 确保n是2的幂次
        if n & (n - 1) != 0:
            # 补零到最近的2的幂次
            next_power = 1
            while next_power < n:
                next_power <<= 1
            data = data + [0] * (next_power - n)
            n = next_power
        
        # 分治FFT
        even = data[::2]
        odd = data[1::2]
        
        even_fft = self.fft(even)
        odd_fft = self.fft(odd)
        
        result = [0] * n
        for k in range(n // 2):
            # 计算旋转因子
            angle = -2 * cmath.pi * k / n
            w = cmath.exp(1j * angle)
            
            # 蝶形运算
            result[k] = even_fft[k] + w * odd_fft[k]
            result[k + n // 2] = even_fft[k] - w * odd_fft[k]
        
        return result
    
    def ifft(self, data: List[complex]) -> List[complex]:
        """
        逆快速傅里叶变换
        
        Args:
            data: 输入数据（复数列表）
            
        Returns:
            IFFT结果
        """
        n = len(data)
        
        # 共轭输入
        conjugated = [x.conjugate() for x in data]
        
        # 正向FFT
        fft_result = self.fft(conjugated)
        
        # 共轭输出并除以n
        result = [x.conjugate() / n for x in fft_result]
        
        return result
    
    def fft_multiply(self, a: List[complex], b: List[complex]) -> List[complex]:
        """
        使用FFT计算多项式乘法
        
        Args:
            a: 第一个多项式的系数
            b: 第二个多项式的系数
            
        Returns:
            乘积多项式的系数
        """
        n = len(a)
        m = len(b)
        
        # 补零到足够长度
        size = 1
        while size < n + m - 1:
            size *= 2
        
        a_padded = a + [0] * (size - n)
        b_padded = b + [0] * (size - m)
        
        # FFT
        a_fft = self.fft(a_padded)
        b_fft = self.fft(b_padded)
        
        # 逐点相乘
        product_fft = [a_fft[i] * b_fft[i] for i in range(size)]
        
        # IFFT
        result = self.ifft(product_fft)
        
        return result
    
    def debug_fft_matching(self, S: str, P: str) -> List[int]:
        """
        调试版本的FFT字符串匹配，用于分析问题
        """
        n, m = len(S), len(P)
        
        if m > n:
            return []
        
        # 编码字符串
        S_encoded = self.encode_string(S)
        P_encoded = self.encode_string(P)
        
        print(f"S编码: {S_encoded}")
        print(f"P编码: {P_encoded}")
        
        # 将模式串反转（用于卷积）
        P_reversed = P_encoded[::-1]
        print(f"P反转: {P_reversed}")
        
        # 转换为复数
        S_complex = [complex(x, 0) for x in S_encoded]
        P_complex = [complex(x, 0) for x in P_reversed]
        
        # 使用FFT计算卷积
        result = self.fft_multiply(S_complex, P_complex)
        
        print(f"卷积结果: {[f'{x.real:.3f}' for x in result]}")
        
        # 提取匹配位置
        matches = []
        for i in range(n - m + 1):
            conv_value = result[i + m - 1].real
            print(f"位置{i}: 卷积值={conv_value:.6f}")
            if abs(conv_value) < 1e-10:
                matches.append(i)
        
        return matches
    
    def is_match_at_position(self, result: List[complex], pos: int, m: int) -> bool:
        """
        判断在指定位置是否匹配
        
        Args:
            result: FFT乘法结果
            pos: 位置
            m: 模式串长度
            
        Returns:
            是否匹配
        """
        if pos >= len(result):
            return False
        
        # 检查卷积结果
        # 对于字符串匹配，我们需要检查卷积值是否满足匹配条件
        value = result[pos]
        
        # 由于我们的编码方式，匹配时卷积值应该是一个特定的值
        # 让我们计算期望的卷积值
        expected_value = 0
        for j in range(m):
            # 这里需要根据具体的编码方式来计算期望值
            # 暂时使用一个简单的判断
            pass
        
        # 简化判断：检查卷积值是否在合理范围内
        return abs(value.real) > 0.1  # 调整阈值
    
    def fft_string_matching(self, S: str, P: str, verbose: bool = True) -> List[int]:
        """
        使用FFT进行字符串匹配
        
        Args:
            S: 主串
            P: 模式串（可包含通配符?）
            verbose: 是否输出详细过程信息
            
        Returns:
            所有匹配位置的列表
        """
        n, m = len(S), len(P)
        
        if verbose:
            print(f"\n=== FFT字符串匹配详细过程 ===")
            print(f"主串 S: '{S}' (长度: {n})")
            print(f"模式串 P: '{P}' (长度: {m})")
        
        if m > n:
            if verbose:
                print("❌ 模式串长度大于主串长度，无法匹配")
            return []
        
        # 编码字符串
        S_encoded = self.encode_string(S)
        P_encoded = self.encode_string(P)
        
        if verbose:
            print(f"\n--- 步骤1: 字符编码 ---")
            print(f"主串编码: {S_encoded}")
            print(f"模式串编码: {P_encoded}")
            print(f"编码规则: 字母a-z → 1-26, 通配符? → 0")
        
        # 对于FFT字符串匹配，我们需要计算多个卷积
        if verbose:
            print(f"\n--- 步骤2: 计算辅助数组 ---")
        
        # 计算S的平方
        S_squared = [x * x for x in S_encoded]
        if verbose:
            print(f"S平方: {S_squared}")
        
        # 计算P的掩码（非通配符位置为1）
        P_mask = [1 if P_encoded[j] != 0 else 0 for j in range(m)]
        if verbose:
            print(f"P掩码: {P_mask} (1表示非通配符位置)")
        
        # 计算P的平方和（只包含非通配符）
        P_squared_sum = sum(P_encoded[j] * P_encoded[j] for j in range(m) if P_encoded[j] != 0)
        if verbose:
            print(f"P平方和: {P_squared_sum}")
        
        # 为卷积计算准备数据
        if verbose:
            print(f"\n--- 步骤3: 准备FFT计算 ---")
        
        # 反转P_mask和P_encoded用于卷积
        P_mask_rev = P_mask[::-1]
        P_encoded_rev = P_encoded[::-1]
        if verbose:
            print(f"P掩码反转: {P_mask_rev}")
            print(f"P编码反转: {P_encoded_rev}")
        
        # 补零到合适的长度（2的幂次）
        size = 1
        while size < n + m - 1:
            size *= 2
        
        if verbose:
            print(f"FFT计算长度: {size} (向上取2的幂次)")
        
        # 补零
        S_squared_padded = S_squared + [0] * (size - n)
        S_encoded_padded = S_encoded + [0] * (size - n)
        P_mask_padded = P_mask_rev + [0] * (size - m)
        P_encoded_padded = P_encoded_rev + [0] * (size - m)
        
        # 转换为复数
        S_squared_complex = [complex(x, 0) for x in S_squared_padded]
        S_encoded_complex = [complex(x, 0) for x in S_encoded_padded]
        P_mask_complex = [complex(x, 0) for x in P_mask_padded]
        P_encoded_complex = [complex(x, 0) for x in P_encoded_padded]
        
        # FFT
        S_squared_fft = self.fft(S_squared_complex)
        S_encoded_fft = self.fft(S_encoded_complex)
        P_mask_fft = self.fft(P_mask_complex)
        P_encoded_fft = self.fft(P_encoded_complex)
        
        # 计算卷积
        if verbose:
            print(f"\n--- 步骤4: FFT卷积计算 ---")
            
        # conv1: S^2与P_mask的卷积
        conv1_fft = [S_squared_fft[i] * P_mask_fft[i] for i in range(size)]
        conv1 = self.ifft(conv1_fft)
        if verbose:
            print(f"卷积1完成: S²与P掩码的卷积")
        
        # conv2: S与P的卷积
        conv2_fft = [S_encoded_fft[i] * P_encoded_fft[i] for i in range(size)]
        conv2 = self.ifft(conv2_fft)
        if verbose:
            print(f"卷积2完成: S与P的卷积")
        
        # 提取匹配位置
        if verbose:
            print(f"\n--- 步骤5: 分析匹配位置 ---")
            print(f"检查{n - m + 1}个可能的匹配位置...")
            
        matches = []
        for i in range(n - m + 1):
            # 计算匹配度：sum((S[i+j] - P[j])^2 * mask[j])
            # = sum(S[i+j]^2 * mask[j]) + sum(P[j]^2 * mask[j]) - 2*sum(S[i+j]*P[j] * mask[j])
            # = conv1[i+m-1] + P_squared_sum - 2*conv2[i+m-1]
            
            match_score = conv1[i + m - 1].real + P_squared_sum - 2 * conv2[i + m - 1].real
            
            # 详细的匹配分析
            if verbose and (abs(match_score) < 1e-6 or i < 3):  # 显示匹配位置或前3个位置
                print(f"\n位置 {i}: S[{i}:{i+m}] = '{S[i:i+m]}'")
                print(f"  与模式 '{P}' 比较:")
                for j in range(m):
                    s_char = S[i+j] if i+j < n else '?'
                    p_char = P[j]
                    if P[j] == '?':
                        status = "✓ (通配符匹配)"
                    elif s_char == p_char:
                        status = "✓ (字符匹配)"
                    else:
                        status = "✗ (不匹配)"
                    print(f"    位置{j}: '{s_char}' vs '{p_char}' - {status}")
                print(f"  匹配度: {match_score:.6f} (接近0表示匹配)")
            
            # 如果匹配度接近0，说明匹配
            if abs(match_score) < 1e-6:
                matches.append(i)
                if verbose:
                    print(f"  ✓ 在位置{i}找到匹配!")
        
        if verbose:
            print(f"\n--- 匹配结果 ---")
            if matches:
                print(f"✓ 找到{len(matches)}个匹配位置: {matches}")
                for pos in matches:
                    print(f"  位置{pos}: '{S[pos:pos+m]}' 匹配模式 '{P}'")
            else:
                print(f"✗ 未找到匹配")
            print(f"\n算法复杂度: O(n log n) = O({n} log {n}) ≈ O({int(n * np.log2(n) if n > 0 else 0)})")
        
        return matches
    
    def naive_string_matching(self, S: str, P: str) -> List[int]:
        """
        朴素字符串匹配算法（用于对比）
        
        Args:
            S: 主串
            P: 模式串
            
        Returns:
            所有匹配位置的列表
        """
        n, m = len(S), len(P)
        matches = []
        
        for i in range(n - m + 1):
            match = True
            for j in range(m):
                if P[j] != '?' and S[i + j] != P[j]:
                    match = False
                    break
            if match:
                matches.append(i)
        
        return matches


def benchmark_algorithms():
    """性能基准测试"""
    print("=== FFT字符串匹配性能测试 ===")
    
    # 测试数据
    test_cases = [
        ("abcdefghijklmnopqrstuvwxyz", "abc"),
        ("a" * 1000 + "bcd" + "a" * 1000, "bcd"),
        ("a" * 5000 + "xyz" + "a" * 5000, "xyz"),
        ("a" * 10000 + "pattern" + "a" * 10000, "pattern"),
    ]
    
    matcher = FFTStringMatcher()
    
    for i, (S, P) in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: S长度={len(S)}, P长度={len(P)}")
        
        # 测试FFT算法
        start_time = time.time()
        fft_matches = matcher.fft_string_matching(S, P)
        fft_time = time.time() - start_time
        
        # 测试朴素算法
        start_time = time.time()
        naive_matches = matcher.naive_string_matching(S, P)
        naive_time = time.time() - start_time
        
        # 验证结果一致性
        assert fft_matches == naive_matches, f"结果不一致: FFT={fft_matches}, 朴素={naive_matches}"
        
        print(f"FFT算法: {fft_time:.6f}s, 匹配位置: {fft_matches}")
        print(f"朴素算法: {naive_time:.6f}s, 匹配位置: {naive_matches}")
        print(f"加速比: {naive_time/fft_time:.2f}x")


def example_usage():
    """详细的使用示例"""
    print("🎯 === FFT字符串匹配详细演示 ===")
    
    matcher = FFTStringMatcher()
    
    # 示例1：基本匹配
    print("\n" + "="*60)
    print("📌 示例1：基本字符串匹配")
    print("="*60)
    S1 = "abcdefghijklmnop"
    P1 = "def"
    matches1 = matcher.fft_string_matching(S1, P1, verbose=True)
    
    # 示例2：带通配符的匹配
    print("\n" + "="*60)
    print("📌 示例2：通配符匹配")
    print("="*60)
    S2 = "abcdefghijklmnop"
    P2 = "c?f"
    matches2 = matcher.fft_string_matching(S2, P2, verbose=True)
    
    # 示例3：多个匹配
    print("\n" + "="*60)
    print("📌 示例3：多个匹配位置")
    print("="*60)
    S3 = "abababab"
    P3 = "aba"
    matches3 = matcher.fft_string_matching(S3, P3, verbose=True)


def complexity_analysis():
    """复杂度分析演示"""
    print("=== 复杂度分析演示 ===")
    
    matcher = FFTStringMatcher()
    sizes = [100, 500, 1000, 2000, 5000]
    
    for n in sizes:
        # 生成测试数据
        S = "a" * n + "pattern" + "a" * n
        P = "pattern"
        
        # 预热
        for _ in range(5):
            matcher.fft_string_matching(S, P)
        
        # 计时
        start_time = time.time()
        for _ in range(10):
            matcher.fft_string_matching(S, P)
        elapsed = time.time() - start_time
        
        print(f"n={n:4d}: {elapsed:.6f}s")
    
    print("\n复杂度验证:")
    for i in range(1, len(sizes)):
        ratio = sizes[i] / sizes[i-1]
        log_ratio = np.log(ratio)
        print(f"n={sizes[i-1]}→{sizes[i]}: 大小比={ratio:.1f}, log比={log_ratio:.2f}")


def demonstration():
    """完整的算法演示"""
    print("🚀 FFT字符串匹配算法演示")
    print("=" * 80)
    print("根据题目要求，展示详细的正则匹配过程")
    print("=" * 80)
    
    # 运行详细示例
    example_usage()
    
    # 性能对比（简化版）
    print("\n" + "="*60)
    print("📊 性能对比分析")
    print("="*60)
    
    matcher = FFTStringMatcher()
    
    # 测试不同规模的字符串
    test_cases = [
        ("abcdefghijklmnopqrstuvwxyz", "def", "小规模测试"),
        ("a" * 100 + "pattern" + "a" * 100, "pattern", "中等规模测试"),
    ]
    
    for S, P, desc in test_cases:
        print(f"\n{desc}: 主串长度={len(S)}, 模式串长度={len(P)}")
        
        # FFT算法
        import time
        start = time.time()
        fft_result = matcher.fft_string_matching(S, P, verbose=False)
        fft_time = time.time() - start
        
        # 朴素算法
        start = time.time()
        naive_result = matcher.naive_string_matching(S, P)
        naive_time = time.time() - start
        
        print(f"FFT算法: {fft_time:.6f}s, 匹配位置: {fft_result}")
        print(f"朴素算法: {naive_time:.6f}s, 匹配位置: {naive_result}")
        if naive_time > 0:
            print(f"结果一致性: {'✓' if fft_result == naive_result else '✗'}")
            speedup = naive_time / fft_time if fft_time > 0 else float('inf')
            print(f"性能对比: {speedup:.2f}x")


if __name__ == "__main__":
    # 运行完整演示
    demonstration()

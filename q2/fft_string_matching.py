"""
基于FFT的正则匹配算法实现

该模块实现了使用快速傅里叶变换（FFT）进行字符串匹配的算法，
支持通配符?，时间复杂度O(n log n)。
"""

import numpy as np
import cmath
from typing import List, Tuple, Dict, Optional
import time
import threading


class MemoryPool:
    """内存池管理，减少GC压力"""
    
    def __init__(self):
        self._complex_arrays: Dict[int, List[complex]] = {}
        self._int_arrays: Dict[int, List[int]] = {}
        self._lock = threading.Lock()
    
    def get_complex_array(self, size: int) -> List[complex]:
        """获取指定大小的复数数组"""
        with self._lock:
            if size not in self._complex_arrays:
                self._complex_arrays[size] = [0+0j] * size
            return self._complex_arrays[size].copy()
    
    def get_int_array(self, size: int) -> List[int]:
        """获取指定大小的整数数组"""
        with self._lock:
            if size not in self._int_arrays:
                self._int_arrays[size] = [0] * size
            return self._int_arrays[size].copy()


class OptimizedFFTStringMatcher:
    """
    优化的基于FFT的字符串匹配器
    
    使用快速傅里叶变换实现字符串匹配，支持通配符。
    包含多种优化策略：迭代式FFT、内存池、自适应策略等。
    """
    
    def __init__(self):
        """初始化优化的FFT字符串匹配器"""
        self.memory_pool = MemoryPool()
        self._twiddle_cache: Dict[int, List[complex]] = {}
        self.use_numpy_threshold = 1024  # 超过此大小使用NumPy FFT
        self.use_fft_threshold = 64      # 超过此大小使用FFT，否则用DFT
    
    def get_twiddle_factors(self, n: int) -> List[complex]:
        """预计算并缓存旋转因子"""
        if n not in self._twiddle_cache:
            factors = []
            for k in range(n // 2):
                angle = -2 * cmath.pi * k / n
                factors.append(cmath.exp(1j * angle))
            self._twiddle_cache[n] = factors
        return self._twiddle_cache[n]
    
    def bit_reverse_permute(self, data: List[complex]) -> None:
        """原地位反转排列"""
        n = len(data)
        j = 0
        for i in range(1, n):
            bit = n >> 1
            while j & bit:
                j ^= bit
                bit >>= 1
            j ^= bit
            if i < j:
                data[i], data[j] = data[j], data[i]
    
    def iterative_fft(self, data: List[complex]) -> List[complex]:
        """
        迭代式FFT实现，避免递归开销
        
        Args:
            data: 输入数据（复数列表）
            
        Returns:
            FFT结果
        """
        n = len(data)
        if n <= 1:
            return data
        
        # 确保n是2的幂次
        if n & (n - 1) != 0:
            next_power = 1
            while next_power < n:
                next_power <<= 1
            data = data + [0] * (next_power - n)
            n = next_power
        
        # 使用内存池获取结果数组
        result = self.memory_pool.get_complex_array(n)
        for i in range(n):
            result[i] = data[i]
        
        # 位反转排列
        self.bit_reverse_permute(result)
        
        # 迭代计算FFT
        length = 2
        while length <= n:
            angle = -2 * cmath.pi / length
            wlen = cmath.exp(1j * angle)
            
            for i in range(0, n, length):
                w = 1
                for j in range(length // 2):
                    u = result[i + j]
                    v = result[i + j + length // 2] * w
                    result[i + j] = u + v
                    result[i + j + length // 2] = u - v
                    w *= wlen
            
            length <<= 1
        
        return result
    
    def naive_dft(self, data: List[complex]) -> List[complex]:
        """
        朴素DFT实现，用于小规模数据
        
        Args:
            data: 输入数据
            
        Returns:
            DFT结果
        """
        n = len(data)
        result = self.memory_pool.get_complex_array(n)
        
        for k in range(n):
            result[k] = 0
            for j in range(n):
                angle = -2 * cmath.pi * k * j / n
                w = cmath.exp(1j * angle)
                result[k] += data[j] * w
        
        return result
    
    def numpy_fft(self, data: List[complex]) -> List[complex]:
        """
        使用NumPy FFT的高度优化实现
        
        Args:
            data: 输入数据
            
        Returns:
            FFT结果
        """
        np_data = np.array(data, dtype=np.complex128)
        result = np.fft.fft(np_data)
        return result.tolist()
    
    def adaptive_fft(self, data: List[complex]) -> List[complex]:
        """
        自适应FFT选择策略
        
        Args:
            data: 输入数据
            
        Returns:
            FFT结果
        """
        n = len(data)
        
        if n <= self.use_fft_threshold:
            return self.naive_dft(data)  # 小规模用DFT
        elif n <= self.use_numpy_threshold:
            return self.iterative_fft(data)  # 中等规模用迭代FFT
        else:
            return self.numpy_fft(data)  # 大规模用NumPy FFT
    
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
        快速傅里叶变换（保持兼容性的接口）
        
        Args:
            data: 输入数据（复数列表）
            
        Returns:
            FFT结果
        """
        # 使用自适应策略选择最优的FFT实现
        return self.adaptive_fft(data)
    
    def ifft(self, data: List[complex]) -> List[complex]:
        """
        逆快速傅里叶变换
        
        Args:
            data: 输入数据（复数列表）
            
        Returns:
            IFFT结果
        """
        n = len(data)
        
        # 对于大规模数据，直接使用NumPy
        if n > self.use_numpy_threshold:
            np_data = np.array(data, dtype=np.complex128)
            result = np.fft.ifft(np_data)
            return result.tolist()
        
        # 共轭输入
        conjugated = [x.conjugate() for x in data]
        
        # 正向FFT
        fft_result = self.adaptive_fft(conjugated)
        
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
    
    def optimized_fft_string_matching(self, S: str, P: str, verbose: bool = True) -> List[int]:
        """
        优化的FFT字符串匹配算法
        
        集成多种优化策略：自适应FFT、内存池、NumPy集成、分块处理
        
        Args:
            S: 主串
            P: 模式串（可包含通配符?）
            verbose: 是否输出详细过程信息
            
        Returns:
            所有匹配位置的列表
        """
        n, m = len(S), len(P)
        
        if verbose:
            print(f"\n=== 优化FFT字符串匹配详细过程 ===")
            print(f"主串 S: '{S}' (长度: {n})")
            print(f"模式串 P: '{P}' (长度: {m})")
        
        # 启发式预处理
        if not self._heuristic_preprocessing(S, P, verbose):
            return []
        
        # 选择最优算法策略
        algorithm_choice = self._select_algorithm_strategy(n, m, verbose)
        
        if algorithm_choice == "numpy":
            return self._numpy_fft_matching(S, P, verbose)
        elif algorithm_choice == "chunked":
            return self._chunked_string_matching(S, P, verbose)
        else:
            return self.fft_string_matching(S, P, verbose)
    
    def _heuristic_preprocessing(self, S: str, P: str, verbose: bool = True) -> bool:
        """启发式预处理，快速排除不可能匹配的情况"""
        n, m = len(S), len(P)
        
        if m > n:
            if verbose:
                print("❌ 模式串长度大于主串长度，无法匹配")
            return False
        
        # 字符频率检查（对于不含通配符的模式）
        if '?' not in P:
            p_chars = set(P)
            s_chars = set(S)
            if not p_chars.issubset(s_chars):
                if verbose:
                    print(f"❌ 模式串包含主串中不存在的字符: {p_chars - s_chars}")
                return False
        
        return True
    
    def _select_algorithm_strategy(self, n: int, m: int, verbose: bool = True) -> str:
        """根据数据规模选择最优算法策略"""
        if n > 10000:
            strategy = "chunked"
        elif n > self.use_numpy_threshold:
            strategy = "numpy"
        else:
            strategy = "standard"
        
        if verbose:
            print(f"\n--- 算法策略选择 ---")
            print(f"数据规模: n={n}, m={m}")
            print(f"选择策略: {strategy}")
            if strategy == "chunked":
                print("  → 使用分块处理策略")
            elif strategy == "numpy":
                print("  → 使用NumPy优化FFT")
            else:
                print("  → 使用标准优化FFT")
        
        return strategy
    
    def _numpy_fft_matching(self, S: str, P: str, verbose: bool) -> List[int]:
        """使用NumPy FFT的高度优化版本"""
        if verbose:
            print(f"\n--- 步骤2: NumPy FFT计算 ---")
        
        n, m = len(S), len(P)
        S_encoded = self.encode_string(S)
        P_encoded = self.encode_string(P)
        
        # 计算辅助数组
        S_squared = [x * x for x in S_encoded]
        P_mask = [1 if P_encoded[j] != 0 else 0 for j in range(m)]
        P_squared_sum = sum(P_encoded[j] * P_encoded[j] for j in range(m) if P_encoded[j] != 0)
        
        # 准备NumPy数组
        size = 1
        while size < n + m - 1:
            size *= 2
        
        # 使用NumPy进行高效计算
        S_squared_np = np.zeros(size, dtype=np.complex128)
        S_encoded_np = np.zeros(size, dtype=np.complex128)
        P_mask_np = np.zeros(size, dtype=np.complex128)
        P_encoded_np = np.zeros(size, dtype=np.complex128)
        
        S_squared_np[:n] = S_squared
        S_encoded_np[:n] = S_encoded
        P_mask_np[:m] = P_mask[::-1]  # 反转
        P_encoded_np[:m] = P_encoded[::-1]  # 反转
        
        # NumPy FFT计算
        S_squared_fft = np.fft.fft(S_squared_np)
        S_encoded_fft = np.fft.fft(S_encoded_np)
        P_mask_fft = np.fft.fft(P_mask_np)
        P_encoded_fft = np.fft.fft(P_encoded_np)
        
        # 卷积计算
        conv1 = np.fft.ifft(S_squared_fft * P_mask_fft)
        conv2 = np.fft.ifft(S_encoded_fft * P_encoded_fft)
        
        # 提取匹配位置
        matches = []
        for i in range(n - m + 1):
            match_score = conv1[i + m - 1].real + P_squared_sum - 2 * conv2[i + m - 1].real
            if abs(match_score) < 1e-6:
                matches.append(i)
        
        if verbose:
            print(f"NumPy FFT计算完成，找到{len(matches)}个匹配")
        
        return matches
    
    def _chunked_string_matching(self, S: str, P: str, verbose: bool, chunk_size: int = 5000) -> List[int]:
        """分块处理长字符串"""
        if verbose:
            print(f"\n--- 步骤2: 分块处理策略 ---")
            print(f"分块大小: {chunk_size}")
        
        matches = []
        m = len(P)
        
        for i in range(0, len(S), chunk_size):
            # 考虑重叠区域以避免跨块匹配丢失
            end = min(i + chunk_size + m - 1, len(S))
            chunk = S[i:end]
            
            if verbose and i == 0:
                print(f"处理第一块: 位置{i}到{end-1}")
            
            # 对块进行FFT匹配
            chunk_matches = self.fft_string_matching(chunk, P, verbose=False)
            
            # 调整匹配位置到全局坐标
            adjusted_matches = [pos + i for pos in chunk_matches if pos + i + m <= len(S)]
            matches.extend(adjusted_matches)
        
        # 去重并排序
        matches = sorted(set(matches))
        
        if verbose:
            print(f"分块处理完成，找到{len(matches)}个匹配")
        
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


# 主类名
FFTStringMatcher = OptimizedFFTStringMatcher


def benchmark_algorithms():
    """FFT字符串匹配算法性能测试"""
    print("=== FFT字符串匹配性能测试 ===")
    
    # 测试数据
    test_cases = [
        ("abcdefghijklmnopqrstuvwxyz", "def", "小规模测试"),
        ("a" * 100 + "pattern" + "a" * 100, "pattern", "中等规模测试"),
        ("a" * 1000 + "bcd" + "a" * 1000, "bcd", "大规模测试"),
        ("a" * 5000 + "xyz" + "a" * 5000, "xyz", "超大规模测试"),
    ]
    
    matcher = FFTStringMatcher()
    
    for i, (S, P, desc) in enumerate(test_cases, 1):
        print(f"\n{desc} {i}: S长度={len(S)}, P长度={len(P)}")
        
        # 测试FFT算法
        start_time = time.time()
        fft_matches = matcher.fft_string_matching(S, P, verbose=False)
        fft_time = time.time() - start_time
        
        # 测试朴素算法
        start_time = time.time()
        naive_matches = matcher.naive_string_matching(S, P)
        naive_time = time.time() - start_time
        
        # 验证结果一致性
        assert fft_matches == naive_matches, \
               f"结果不一致: FFT={fft_matches}, 朴素={naive_matches}"
        
        print(f"FFT算法: {fft_time:.6f}s, 匹配位置: {fft_matches}")
        print(f"朴素算法: {naive_time:.6f}s")
        
        if naive_time > 0:
            speedup = naive_time / fft_time if fft_time > 0 else float('inf')
            print(f"相对朴素算法加速比: {speedup:.2f}x")


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
    
    matcher = OptimizedFFTStringMatcher()
    
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
    
    matcher = OptimizedFFTStringMatcher()
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
    
    matcher = OptimizedFFTStringMatcher()
    
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


def demonstration():
    """FFT字符串匹配算法完整演示"""
    print("🚀 FFT字符串匹配算法演示")
    print("=" * 80)
    print("展示基于FFT的正则匹配过程")
    print("=" * 80)
    
    matcher = FFTStringMatcher()
    
    # 示例1：展示自适应策略选择
    print("\n" + "="*60)
    print("📌 示例1：自适应策略演示")
    print("="*60)
    
    test_cases = [
        ("abcdefghijklmnop", "def", "小规模数据"),
        ("a" * 200 + "pattern" + "a" * 200, "pattern", "中规模数据"),
        ("a" * 2000 + "target" + "a" * 2000, "target", "大规模数据"),
    ]
    
    for S, P, desc in test_cases:
        print(f"\n{desc}: 长度={len(S)}")
        matches = matcher.fft_string_matching(S, P, verbose=True)
        print(f"匹配结果: {matches}")
    
    # 示例2：性能对比
    print("\n" + "="*60)
    print("📊 示例2：性能对比分析")
    print("="*60)
    benchmark_algorithms()
    
    # 示例3：通配符匹配
    print("\n" + "="*60)
    print("📌 示例3：通配符匹配")
    print("="*60)
    S3 = "abcdefghijklmnopqrstuvwxyz"
    P3 = "c?e?g"
    print(f"测试字符串: '{S3}'")
    print(f"模式串: '{P3}'")
    matches3 = matcher.fft_string_matching(S3, P3, verbose=True)


if __name__ == "__main__":
    # 运行FFT字符串匹配算法演示
    demonstration()

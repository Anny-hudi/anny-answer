#!/usr/bin/env python3

from fft_string_matching import FFTStringMatcher

def main():
    matcher = FFTStringMatcher()
    
    # 测试基本匹配
    S = "abcdefghijklmnop"
    P = "def"
    
    print(f"主串: {S}")
    print(f"模式: {P}")
    
    try:
        # 先运行调试版本
        print("=== 调试信息 ===")
        debug_matches = matcher.debug_fft_matching(S, P)
        print(f"调试匹配位置: {debug_matches}")
        
        print("\n=== 正式版本 ===")
        matches = matcher.fft_string_matching(S, P)
        print(f"匹配位置: {matches}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

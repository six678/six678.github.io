import csv
import datetime
import os
import itertools
from multiprocessing import Pool, cpu_count
import json

# 复刻核心算法类（为了性能和独立运行，这里包含精简版逻辑）
class FastLotteryEngine:
    def __init__(self, file_path='data.json'):
        self.records = []
        self.date_to_index = {}
        self.all_numbers = list(range(1, 50))
        self.load_data(file_path)

    def load_data(self, file_path):
        if not os.path.exists(file_path):
            return
        
        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                data = json.load(f)
                
            temp_records = []
            for item in data:
                open_time = item.get('openTime')
                open_code = item.get('openCode')
                if not open_time or not open_code:
                    continue
                
                # 提取日期 (YYYY-MM-DD)
                date_str = open_time.split(' ')[0]
                
                try:
                    num_parts = open_code.split(',')
                    nums = [int(n.strip()) for n in num_parts]
                    if len(nums) >= 7:
                        temp_records.append({'date': date_str, 'nums': nums})
                except:
                    continue
            
            # 升序排列方便计算
            self.records = sorted(temp_records, key=lambda x: x['date'])
            self.date_to_index = {r['date']: i for i, r in enumerate(self.records)}
        except Exception as e:
            print(f"解析 JSON 出错: {e}")

    def get_offset_record(self, date, offset):
        idx = self.date_to_index.get(date)
        if idx is None: return None
        target_idx = idx + offset
        if 0 <= target_idx < len(self.records):
            return self.records[target_idx]
        return None

    def backtest(self, start_date, end_date, p):
        """核心回测函数"""
        start_off = p['startOffsetDays']
        refer_off = p['referOffsetDays']
        excl_days = p['excludingDays']
        excl_off = p['excludingOffsetDays']
        is_reverse = p.get('isReverse', False)
        target_pos = p.get('targetPos', 6) # 默认特码
        
        hit_odds = 47
        amount = 50
        
        total_profit = 0
        hit_count = 0
        total_games = 0
        
        # 预筛选范围
        target_indices = [i for i, r in enumerate(self.records) if start_date <= r['date'] <= end_date]
        
        for idx in target_indices:
            current_record = self.records[idx]
            
            # 1. 参考
            refer_rec = self.get_offset_record(current_record['date'], -start_off)
            if not refer_rec: continue
            refer_num = refer_rec['nums'][target_pos]
            
            # 2. 搜索
            search_start_rec = self.get_offset_record(refer_rec['date'], -refer_off)
            if not search_start_rec: continue
            
            search_start_idx = self.date_to_index[search_start_rec['date']]
            excl_refer_date = None
            for i in range(search_start_idx, -1, -1):
                if self.records[i]['nums'][target_pos] == refer_num:
                    excl_refer_date = self.records[i]['date']
                    break
            if not excl_refer_date: continue
            
            # 3. 排除起点
            excl_ref_idx = self.date_to_index[excl_refer_date]
            index_gap = excl_ref_idx - idx
            actual_offset = max(-excl_off, index_gap + 1)
            
            excl_start_rec = self.get_offset_record(excl_refer_date, actual_offset)
            if not excl_start_rec: continue
            
            # 4. 排除集
            excl_set = set()
            es_idx = self.date_to_index[excl_start_rec['date']]
            for i in range(es_idx, max(-1, es_idx - excl_days), -1):
                excl_set.add(self.records[i]['nums'][target_pos])
            
            # 5. 命中判定
            final_nums_count = len(excl_set) if is_reverse else (49 - len(excl_set))
            if final_nums_count == 0: continue
            
            target_num = current_record['nums'][target_pos]
            is_hit = target_num in excl_set if is_reverse else target_num not in excl_set
            
            if is_hit:
                hit_count += 1
                total_profit += amount * (hit_odds - final_nums_count)
            else:
                total_profit -= amount * final_nums_count
            
            total_games += 1
            
        return {
            'profit': total_profit,
            'hit_rate': (hit_count / total_games * 100) if total_games > 0 else 0,
            'games': total_games,
            'params': p
        }

# 多进程包装器
def worker(task):
    engine, start_date, end_date, p = task
    result = engine.backtest(start_date, end_date, p)
    return result

if __name__ == '__main__':
    engine = FastLotteryEngine('data.json')
    if not engine.records:
        print("错误: 无法加载数据")
        exit()

    print(f"数据加载完成: {len(engine.records)} 条")
    
    # 定义搜索网格
    # 请根据需要调整范围，范围越大耗时越久
    grid = {
        'startOffsetDays': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'referOffsetDays': [10, 20, 30, 40, 50],
        'excludingDays': [10, 20, 30, 40, 50],
        'excludingOffsetDays': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'isReverse': [False, True],
        'targetPos': [0, 1, 2, 3, 4, 5, 6] # 平码 1-6 + 特码
    }
    
    # 组合所有参数
    keys = grid.keys()
    combinations = [dict(zip(keys, v)) for v in itertools.product(*grid.values())]
    
    print(f"总计组合数: {len(combinations)} (7个位置并行)")
    print(f"开始使用 {cpu_count()} 个核心并行回测...")
    
    start_time = datetime.datetime.now()
    
    # 固定回测范围 (例如最近一年)
    b_start = "2025-01-01"
    b_end = datetime.datetime.now().strftime('%Y-%m-%d')

    tasks = [(engine, b_start, b_end, p) for p in combinations]
    
    with Pool(processes=cpu_count()) as pool:
        all_results = pool.map(worker, tasks)
    
    # 排序结果 (按利润)
    all_results.sort(key=lambda x: x['profit'], reverse=True)
    
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"回测完成，耗时: {duration:.2f} 秒")
    print("\n--- 全位置前 5 名最佳策略 ---")
    print(f"{'位置':>4} | {'利润':>10} | {'胜率':>8} | {'参数组合'}")
    print("-" * 80)
    
    for r in all_results[:5]:
        p = r['params']
        p_str = f"sOff:{p['startOffsetDays']}, rOff:{p['referOffsetDays']}, eD:{p['excludingDays']}, eO:{p['excludingOffsetDays']}"
        pos_label = f"平{p['targetPos']+1}" if p['targetPos'] < 6 else "特"
        print(f"{pos_label:>4} | {r['profit']:>10.0f} | {r['hit_rate']:>7.2f}% | {p_str}")

    # 保存到 CSV (包含位置列)
    with open('optimization_results.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Profit', 'HitRate', 'Games', 'targetPos', 'startOffsetDays', 'referOffsetDays', 'excludingDays', 'excludingOffsetDays', 'isReverse'])
        for r in all_results:
            p = r['params']
            writer.writerow([r['profit'], r['hit_rate'], r['games'], p['targetPos'], p['startOffsetDays'], p['referOffsetDays'], p['excludingDays'], p['excludingOffsetDays'], p['isReverse']])
    
    print(f"\n完整结果已保存至: optimization_results.csv (包含所有位置数据)")

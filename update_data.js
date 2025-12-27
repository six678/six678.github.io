// update_data.js 
const fs = require('fs');

async function updateData() {
    try {
        console.log("开始更新数据...");
        
        // 1. 读取仓库中现有的数据 (保留旧数据)
        let oldData = [];
        if (fs.existsSync('data.json')) {
            const content = fs.readFileSync('data.json', 'utf8');
            oldData = content ? JSON.parse(content) : [];
        }

        // 2. 抓取最新一期 (Live Data)
        console.log("正在抓取最新直播数据...");
        const liveRes = await fetch('https://macaumarksix.com/api/live2');
        const liveData = await liveRes.json();

        // 3. 循环抓取从 2020 年到当前年份的历史数据
        const startYear = 2020;
        const currentYear = new Date().getFullYear();
        let allHistoryData = [];

        for (let year = startYear; year <= currentYear; year++) {
            console.log(`正在抓取 ${year} 年历史数据...`);
            try {
                const historyRes = await fetch(`https://history.macaumarksix.com/history/macaujc2/y/${year}`);
                const historyJson = await historyRes.json();
                
                if (historyJson && historyJson.data) {
                    allHistoryData = allHistoryData.concat(historyJson.data);
                    console.log(`成功获取 ${year} 年数据：${historyJson.data.length} 条`);
                }
            } catch (err) {
                console.error(`抓取 ${year} 年数据失败:`, err.message);
                // 某一年失败可以选择跳过或停止
            }
        }

        // 4. 合并所有数据并去重
        // 优先级：liveData > historyData > oldData (靠前的覆盖靠后的)
        const combined = [...liveData, ...allHistoryData, ...oldData];
        
        // 使用 Map 以 'expect' 为键去重
        const uniqueDataMap = new Map();
        combined.forEach(item => {
            if (item && item.expect) {
                // 如果 Map 中还不存在该期号，则存入
                if (!uniqueDataMap.has(item.expect)) {
                    uniqueDataMap.set(item.expect, item);
                }
            }
        });

        const uniqueData = Array.from(uniqueDataMap.values());

        // 5. 排序 (按期号 expect 降序排列，最新的在前面)
        uniqueData.sort((a, b) => {
            return parseInt(b.expect) - parseInt(a.expect);
        });

        // 6. 写入文件
        fs.writeFileSync('data.json', JSON.stringify(uniqueData, null, 2));
        
        console.log(`--------------------------------------`);
        console.log(`数据更新完成！当前总记录数：${uniqueData.length}`);
    } catch (e) {
        console.error("更新过程中出现严重错误:", e);
        process.exit(1);
    }
}

updateData();

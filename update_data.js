// update_data.js 建议逻辑  
const fs = require('fs');  
  
async function updateData() {  
    try {  
        // 1. 读取仓库中现有的数据 (为了保留往年数据)  
        let oldData = [];  
        if (fs.existsSync('data.json')) {  
            oldData = JSON.parse(fs.readFileSync('data.json', 'utf8'));  
        }  
  
        // 2. 抓取最新一期  
        const liveRes = await fetch('https://macaumarksix.com/api/live2');  
        const liveData = await liveRes.json();  
  
        // 3. 抓取今年历史  
        const year = new Date().getFullYear();  
        const historyRes = await fetch(`https://history.macaumarksix.com/history/macaujc2/y/${year}`);  
        const historyJson = await historyRes.json();  
        const historyData = historyJson.data || [];  
  
        // 4. 合并所有数据并去重  
        const combined = [...liveData, ...historyData, ...oldData];  
        const uniqueData = Array.from(new Map(combined.map(item => [item.expect, item])).values());  
  
        // 5. 排序  
        uniqueData.sort((a, b) => b.expect - a.expect);  
  
        fs.writeFileSync('data.json', JSON.stringify(uniqueData, null, 2));  
    } catch (e) {  
        console.error(e);  
        process.exit(1);  
    }  
}  
updateData();  

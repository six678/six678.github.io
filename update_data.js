const fs = require('fs');  
  
async function updateData() {  
    try {  
        // 1. 抓取最新一期  
        const liveRes = await fetch('https://macaumarksix.com/api/live2');  
        const liveData = await liveRes.json();  
  
        // 2. 抓取今年历史纪录 (2025)  
        const year = new Date().getFullYear();  
        const historyRes = await fetch(`https://history.macaumarksix.com/history/macaujc2/y/${year}`);  
        const historyJson = await historyRes.json();  
        const historyData = historyJson.data || [];  
  
        // 3. 合并并去重 (使用 expect 作为唯一键)  
        const combined = [...liveData, ...historyData];  
        const uniqueData = Array.from(new Map(combined.map(item => [item.expect, item])).values());  
  
        // 4. 按期数降序排列  
        uniqueData.sort((a, b) => b.expect - a.expect);  
  
        // 5. 写入文件  
        fs.writeFileSync('data.json', JSON.stringify(uniqueData, null, 2));  
        console.log(`成功更新数据，当前共有 ${uniqueData.length} 条记录`);  
    } catch (error) {  
        console.error('更新失败:', error);  
        process.exit(1);  
    }  
}  
  
updateData();  

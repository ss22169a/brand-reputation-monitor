# 詞庫維護指南 📚

簡單直覺的詞庫管理系統 — 隨時新增、編輯、刪除詞彙

---

## 快速開始

### 1. 啟動後端服務

```bash
cd backend/api
python main.py
```

服務會在 `http://localhost:8000` 啟動

### 2. 打開詞庫後台

在瀏覽器中打開：
```
http://localhost:8000/docs  # 查看 API 文檔（FastAPI自動生成）

或直接打開 HTML 介面：
../frontend/keywords_admin.html
```

或者用簡單的方法直接打開 HTML 文件（需確保後端正在運行）

---

## 使用方式

### 四個詞庫分類

| 分類 | 說明 | 例子 |
|------|------|------|
| **🚨 危機警示 (CRITICAL)** | 品牌形象受損的詞彙 | 壞掉、受騙、炎上 |
| **📉 情感轉向 (STRATEGIC)** | 忠誠度下滑的詞彙 | 變貴了、以前比較好 |
| **⚙️ 使用痛點 (OPERATIONAL)** | 產品/服務改進的詞彙 | 找不到、卡住、很難用 |
| **🎯 關鍵商機 (OPPORTUNITIES)** | 銷售轉化的詞彙 | 敲碗、哪裡買、想入坑 |

### 後台介面操作

#### ✅ 新增詞

1. 在對應分類卡片下的輸入框輸入新詞
2. 設置權重（0.5～2.0，默認1）
3. 點擊「新增」或按 Enter

![新增詞庫](./docs/add-keyword.png)

#### ✏️ 編輯詞

1. 點擊詞旁的「編輯」按鈕
2. 修改權重
3. 點擊「保存」

#### 🗑️ 刪除詞

1. 點擊詞旁的「刪除」按鈕
2. 確認刪除

#### 🔍 搜尋詞

1. 在頂部搜尋框輸入關鍵字
2. 點擊「搜尋」
3. 結果會即時顯示在各分類中

---

## 詞庫權重說明

**權重 (Weight)：** 詞在分類判定中的重要性

- **2.0** = 高度重要（強烈信號）
- **1.5** = 中度重要
- **1.0** = 標準重要性（默認）
- **0.5** = 輔助信號

### 何時調整權重？

假設「爆單」應該是 OPPORTUNITIES（商機），而你發現它被誤分為 CRITICAL（危機）：

1. 移除「爆單」從 CRITICAL
2. 新增「爆單」到 OPPORTUNITIES，權重設為 1.5
3. 測試新的分類結果

---

## API 端點

如果你想用程式碼直接操作詞庫：

### 獲取所有詞庫
```bash
curl http://localhost:8000/api/keywords/all
```

### 新增詞
```bash
curl -X POST http://localhost:8000/api/keywords/add \
  -H "Content-Type: application/json" \
  -d '{"category": "CRITICAL", "word": "新詞", "weight": 1.5}'
```

### 更新詞
```bash
curl -X POST http://localhost:8000/api/keywords/update \
  -H "Content-Type: application/json" \
  -d '{"category": "CRITICAL", "word": "新詞", "weight": 2}'
```

### 刪除詞
```bash
curl -X POST http://localhost:8000/api/keywords/delete \
  -H "Content-Type: application/json" \
  -d '{"category": "CRITICAL", "word": "新詞"}'
```

### 搜尋詞
```bash
curl "http://localhost:8000/api/keywords/search?q=壞"
```

### 統計數據
```bash
curl http://localhost:8000/api/keywords/stats
```

---

## 檔案結構

```
backend/
├── api/
│   ├── main.py                 # FastAPI 主應用（已整合 keywords 路由）
│   ├── routes/
│   │   └── keywords.py         # 詞庫 API 路由 ✨ 新文件
│   └── nlp/
│       ├── keywords_config.py  # Python 配置（自動同步更新）
│       └── sentiment.py        # 情感分析引擎
├── data/
│   └── keywords.json           # 詞庫數據（JSON 格式） ✨ 新文件
│
frontend/
└── keywords_admin.html         # 後台管理介面 ✨ 新文件
```

---

## 自動同步機制

✨ **智能同步**

- 每當你在後台修改詞庫時，系統會自動：
  1. 保存到 `backend/data/keywords.json`
  2. 同步更新 `backend/api/nlp/keywords_config.py`
  3. 新詞立即對 sentiment analyzer 生效

無需手動更新配置文件！

---

## 常見操作流程

### 場景 1：發現誤分的詞

**問題：** "爆單" 被判成 CRITICAL，但應該是 OPPORTUNITIES

**解決方案：**
1. 打開後台
2. 在 CRITICAL 找到 "爆單"，點擊「刪除」
3. 到 OPPORTUNITIES，新增 "爆單"，權重設為 1.5
4. 重新測試分類 ✓

### 場景 2：加入新客戶反饋中的詞

**問題：** 客戶提到 "卡頓"，但詞庫中沒有

**解決方案：**
1. 打開後台
2. 到 OPERATIONAL，新增 "卡頓"，權重設為 1
3. 立即生效，無需重啟服務 ✓

### 場景 3：調整權重以優化準確度

**問題：** "等超久" 有時被當成 CRITICAL，但大多數應該是 STRATEGIC

**解決方案：**
1. 在 CRITICAL 找到 "等超久"，點擊「編輯」
2. 權重改為 1（降低優先級）
3. 保存 ✓

---

## 月度審查清單

每月 1 日建議做一次完整審查（5-10 分鐘）：

- [ ] 搜尋 5-10 個品牌，檢查是否有誤分
- [ ] 記錄誤分的詞
- [ ] 查詢客戶反饋中新出現的詞
- [ ] 新增或移動誤分的詞
- [ ] 調整權重以提升準確度
- [ ] 檢查誤分率是否下降

範例記錄：

```
【2026-03-01 審查紀錄】
✓ 新增: 爆單(1.5)、卡頓(1)、沒貨(1)
✓ 移動: 等超久 CRITICAL→STRATEGIC (1→1.5)
✓ 刪除: (無)
誤分率: 8% → 5% ✓
```

---

## 數據備份

詞庫數據存儲在：
- `backend/data/keywords.json` — 主要備份
- `backend/api/nlp/keywords_config.py` — Python 配置版本

建議定期提交到 Git：

```bash
cd /Users/sylvia/.openclaw/workspace/brand-reputation-monitor
git add backend/data/keywords.json
git commit -m "詞庫更新：新增3個詞，調整權重"
git push origin main
```

---

## 故障排除

### 問題：後台無法連接到 API

**原因：** 後端服務未運行或 API_BASE 地址錯誤

**解決：**
1. 確保 `python main.py` 在運行
2. 檢查 HTML 中的 `API_BASE` 變數是否正確（預設 `http://localhost:8000`）
3. 檢查防火牆是否阻擋 8000 端口

### 問題：新增詞後分析還是不生效

**原因：** 可能是句子中有多個詞，其他詞權重更高

**解決：**
1. 增加新詞的權重
2. 確認新詞確實被同步到 `keywords_config.py`
3. 重啟情感分析引擎（或重啟應用）

### 問題：JSON 格式錯誤

**症狀：** API 返回錯誤，詞庫無法加載

**解決：**
1. 打開 `backend/data/keywords.json`
2. 用線上 JSON 驗證器檢查格式：https://jsonlint.com/
3. 找到錯誤位置並修正
4. 重新啟動後端

---

## 聯繫與反饋

如果詞庫系統有問題或建議，歡迎反饋！

當前版本：**1.0** | 最後更新：**2026-03-01**

---

**提示：** 詞庫是品牌監控系統的心臟。定期維護會顯著提升分類準確度！ 🎯

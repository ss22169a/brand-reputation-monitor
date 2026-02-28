# 版本管理

## 版本命名規則

- **主版本 (Major)**：1.x.x — 系統架構大改
- **次版本 (Minor)**：x.1.x — 新功能或重要修復
- **修訂版 (Patch)**：x.x.1 — 小改進、詞庫更新、bug 修復

---

## 版本歷史

### v1.0.0 (2026-03-01)
**初始版本**
- ✅ 詞庫維護系統完成（222 個詞彙）
- ✅ 四級優先級分類（Critical/Strategic/Operational/Opportunities）
- ✅ 後台詞庫編輯介面
- ✅ API 自動同步到分析系統
- ✅ 品牌口碑監控前端
- ✅ 情感分析和優先級排序
- 🔧 修復詞庫載入邏輯

---

## 如何更新版本

### 步驟 1：修改 VERSION 文件
```bash
echo "1.0.1" > VERSION
```

### 步驟 2：更新 CHANGELOG.md
在「版本歷史」區段頂部添加新版本條目

### 步驟 3：提交和推送
```bash
git add VERSION CHANGELOG.md <其他改動的文件>
git commit -m "版本 1.0.1：<改動說明>"
git push origin main
```

---

## 常見更新場景

| 場景 | 版本號變化 |
|------|----------|
| 詞庫新增 5+ 詞彙 | Patch (x.x.+1) |
| 新增功能模塊 | Minor (x.+1.0) |
| UI 大改設計 | Minor (x.+1.0) |
| 系統架構重構 | Major (+1.0.0) |
| 修復 bug | Patch (x.x.+1) |
| 性能優化 | Patch (x.x.+1) |

---

## 發布清單

每個版本發布時確認：

- [ ] VERSION 文件已更新
- [ ] CHANGELOG.md 已更新
- [ ] 本地測試正常（http://localhost:8000）
- [ ] Git 已提交並推送
- [ ] Render 部署成功
- [ ] 生產環境測試通過


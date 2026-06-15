# 考研作战地图

> 2026 考研 · 总览与进度追踪

## 目标

- **目标院校**：
- **目标专业**：
- **考试时间**：2026年12月下旬（预计）

## 各科进度

### 政治
- [ ] 基础阶段
- [ ] 强化阶段
- [ ] 冲刺阶段

### 英语
- [ ] 单词（长期）
- [ ] 阅读专项
- [ ] 写作专项

### 数学
- [ ] 基础阶段
- [ ] 强化阶段
- [ ] 真题阶段

### 专业课
- [ ] 教材通读
- [ ] 重点整理
- [ ] 真题练习

---

## 政治笔记

```dataviewjs
const pages = dv.pages('"03_LIFE/考研/政治"').sort(p => p.file.mtime, 'desc')
if (pages.length === 0) {
  dv.paragraph("*暂无笔记，新建笔记后自动出现*")
} else {
  dv.list(pages.map(p => `[[${p.file.name}]] · ${dv.date(p.file.mtime).toFormat("yyyy-MM-dd")}`))
}
```

## 英语笔记

```dataviewjs
const pages = dv.pages('"03_LIFE/考研/英语"').sort(p => p.file.mtime, 'desc')
if (pages.length === 0) {
  dv.paragraph("*暂无笔记，新建笔记后自动出现*")
} else {
  dv.list(pages.map(p => `[[${p.file.name}]] · ${dv.date(p.file.mtime).toFormat("yyyy-MM-dd")}`))
}
```

## 数学笔记

```dataviewjs
const pages = dv.pages('"03_LIFE/考研/数学"').sort(p => p.file.mtime, 'desc')
if (pages.length === 0) {
  dv.paragraph("*暂无笔记，新建笔记后自动出现*")
} else {
  dv.list(pages.map(p => `[[${p.file.name}]] · ${dv.date(p.file.mtime).toFormat("yyyy-MM-dd")}`))
}
```

## 专业课笔记

```dataviewjs
const pages = dv.pages('"03_LIFE/考研/专业课"').sort(p => p.file.mtime, 'desc')
if (pages.length === 0) {
  dv.paragraph("*暂无笔记，新建笔记后自动出现*")
} else {
  dv.list(pages.map(p => `[[${p.file.name}]] · ${dv.date(p.file.mtime).toFormat("yyyy-MM-dd")}`))
}
```

## 复习计划 & 阶段复盘

```dataviewjs
const pages = dv.pages('"03_LIFE/考研/复习计划"').sort(p => p.file.mtime, 'desc')
if (pages.length === 0) {
  dv.paragraph("*暂无笔记，新建笔记后自动出现*")
} else {
  dv.list(pages.map(p => `[[${p.file.name}]] · ${dv.date(p.file.mtime).toFormat("yyyy-MM-dd")}`))
}
```

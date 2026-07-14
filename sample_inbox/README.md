# 把散落的文档丢这里

把博主散落在各处的成交确认书、豪宅推介、土拍纪要等文件（PDF / Word / PPT）放进本文件夹，然后运行：

```bash
cd backend
python -m ingestion.extractor ../sample_inbox
```

系统会自动解析、抽取结构化数据并入库，同时触发协同（自动选题、客户评分等）。

> 本文件夹仅作示例输入目录，实际文件不纳入版本管理。

# FemAI 飞书群聊导出指南

## 方法一：飞书桌面端导出（推荐）

### 步骤

1. 打开飞书桌面版（Mac / Windows）

2. 进入群聊：FemAI 学习群

3. 点击右上角的 `⋯`（更多菜单）

4. 选择 **「导出聊天记录」** 或 **「保存聊天记录」**

   > 💡 如果选项不在菜单中，试试：
   > - 点击群聊名称进入群设置
   > - 在「聊天管理」中找到导出选项

5. 选择导出格式：
   - ✅ **纯文本 (.txt)** — 推荐，pipeline 直接支持
   - ✅ **CSV (.csv)** — 也支持

6. 将导出的文件放到：
   ```
   /Users/sophia/Desktop/AI学习库/raw-feishu/
   ```

7. 重新运行 pipeline：
   ```bash
   cd /Users/sophia/Desktop/AI学习库
   python3 run_pipeline.py --skip-llm
   ```

---

## 方法二：手动复制（少量消息时）

1. 在飞书群聊中，选中并复制你需要的内容
2. 打开文本编辑器，粘贴
3. 保存为：
   ```
   /Users/sophia/Desktop/AI学习库/raw-feishu/feishu_manual_export.txt
   ```

---

## 方法三：API 方式（需管理员配合）

如果后续可以添加机器人到群聊，pipelinel 已内置 API 支持：

1. 在 [飞书开放平台](https://open.feishu.cn/) 确保应用已添加 `im:message` 权限
2. 将机器人添加到群聊：群设置 → 添加机器人 → 选择你的应用
3. 设置环境变量：
   ```bash
   export FEISHU_APP_ID="你的 App ID"
   export FEISHU_APP_SECRET="你的 App Secret"
   ```
4. 运行：
   ```bash
   python3 run_pipeline.py
   ```

---

## 注意事项

- 文件名**不要以 `_` 开头**（pipeline 会跳过控制文件 `_xxx.json`）
- 支持的文件后缀：`.txt`, `.csv`
- 导出后 pipeline 会自动清洗为标准格式

# Zulip 官方帮助文档快照

本学习项目使用 Zulip 官方开源仓库的 27 篇帮助文档，内容为英文，可使用 BGE-M3 进行中文跨语言检索，再由 DeepSeek 用中文回答。

- 来源：https://github.com/zulip/zulip
- 固定版本：`dc257d7c3516fa1da4a52eedf694cb7733819a0d`
- 获取日期：2026-10-13。计费等规则以该快照为准，不保证与未来线上政策一致。
- 许可：Apache-2.0；完整原始声明见 [LICENSE](upstream/LICENSE)、[NOTICE](upstream/NOTICE)。本项目与 Zulip 无隶属关系。

`documents/` 是实际参与检索的 27 篇 Markdown；`manifest.json` 记录每篇文档的标题、官方链接、固定版本链接与 SHA256。`upstream/` 保留原始 MDX、引用片段、导航组件和许可文件，`upstream-lock.json` 记录原始 Git blob 哈希。引用片段、许可文件和切分后的 chunk 均不计作独立文档。

转换由 `python -m scripts.build_corpus` 完成：验证源文件哈希，展开 MDX 引用，将平台标签、设置导航等组件转为文字，移除相关文章导航。每篇转换文档均标记修改说明。不执行源文件中的 JavaScript。

## 增补自己的资料

将有权使用的 UTF-8 Markdown/TXT 放入 `documents/`，重新运行 `python -m scripts.ingest_documents` 并重启服务即可。已有文档可以修改或移除，索引指纹会变化；服务只查询当前指纹对应的集合，旧集合不会混入结果。若希望提供公开来源，按现有格式补充 manifest；没有公开链接的本地资料仍可通过页面浏览正文。

原始文件、中文评测问题和向量索引分开存放。评测题不写入知识库，防止将测试题本身当作检索证据。

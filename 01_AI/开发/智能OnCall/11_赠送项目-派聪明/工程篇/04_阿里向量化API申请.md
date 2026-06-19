# ✅阿里向量化 API 申请，附豆包 embedding

- 章节难度：★☆☆☆☆ \- 简单

- 项目名称：派聪明 RAG 知识库

原来我们这里用的是豆包的 embedding，但豆包突然下架了 241505 模型，导致大家在向量的时候直接干懵逼了，报错了，真的非常离谱。如果让字节去做 JDK，那 Java 真活不到现在，一个模型下架，最起码新的模型是要适配旧的向量维度的，豆包新的模型直接把 2048 干掉了，那和 ES 的维度就不一样了，真的离谱。

所以我加急申请了阿里的 embedding 模型，因为阿里明确了向下兼容，维度参数支持 1024、2048 等。

![[UxkobKWt0oqkKMxAB31cullKnxe.png]]

[登录阿里百炼 ](https://my.feishu.cn/https%3A%2F%2Fbailian.console.aliyun.com%2F%3Ftab%3Dmodel%23%2Fapi-key)，申请 API key，然后复制，随后需要复制到 application\.yml 中：

![[TRC6b5Zopo3c54xfQBDcqVqonob.png]]

[在这里可以查看 ](https://my.feishu.cn/https%3A%2F%2Fbailian.console.aliyun.com%2F%3Ftab%3Dmodel%23%2Fmodel-market%3Fcapabilities%3D%255B%2522TR%2522%255D%26z_type_%3D%257B%2522capabilities%2522%253A%2522array%2522%257D)通用文本向量\-v4

![[SzwxbUD6yoouCpxtKfNcFPPon0f.png]]

![[YlKBbFGTbod4VVxYzuEckLmznXg.png]]

![[IlDMbKAeSoLhPtxQYOIcYpQxnDc.png]]

![[S9WObLeRJozZPbxR9DhcKHZznCq.png]]

\-\-以下暂时废弃，留作备用\-\-\-\-

向量化这一趴我们用的是豆包的 embedding： [账号登录\-火山引擎](https://my.feishu.cn/https%3A%2F%2Fconsole.volcengine.com%2Fark%2Fregion%3Aark%2Bcn-beijing%2Fmodel%2Fdetail%3FId%3Ddoubao-embedding-vision)\.

![[XrdwbUelNoZSfExPlAycvvaensc.png]]

在 [火山引擎这里找到 api key 管理](https://my.feishu.cn/https%3A%2F%2Fconsole.volcengine.com%2Fark%2Fregion%3Aark%2Bcn-beijing%2FapiKey%3Fapikey%3D%257B%257D)

![[NLyabHVuzo7eSqxIBfEcxL04nDd.png]]

然后记得复制它。

然后再开通管理这里找到第二个 doubao\-embedding 开通它。

![[NZfQbM1aAo3Bhkxu1pRcuUrQnIb.png]]

**同样记得充值。 **。

把你刚刚复制的 key 复制粘贴到这里。

![[FIZub3EnToqX0PxdO0icZ7NPnEf.png]]

# 错误码说明

| 错误码 | 含义 | 建议排查 |
| --- | --- | --- |
| SIGN_INVALID | 签名校验失败 | 检查参数排序、编码方式、timestamp 是否过期、appid 与环境是否匹配 |
| CALLBACK_TIMEOUT | 回调超时 | 检查回调地址是否可访问、第三方服务是否返回 2xx |
| APP_NOT_FOUND | appid 不存在 | 检查 appid 是否正确、是否使用了错误环境 |
| PARAM_MISSING | 必填参数缺失 | 按接口文档检查缺失字段 |

## Action  

便捷的快速启动栏  

### 使用教程  

| 按键 | 说明 |
| ---- | ---- |
|`Alt` + `p`| 唤醒 |
|`Esc`| 放弃输入并隐藏程序 |
|键入`exit`| 退出程序 |
|回车`Enter`| 执行左侧的命令 |
|`Tab`| 高亮选中并补全 |
|`ctrl`+`u`| 清除左侧输入 |
|`ctrl`+`v`| 粘贴粘贴板内容 |
|右方向键| 下一个 |
|左方向键| 上一个 |
|下方向键| 下一个 |
|上方向键| 上一个 |
|单击鼠标左键| 执行选中的程序 |
|单击鼠标右键| 把程序名复制到粘贴板 |

### 配置教程  

配置信息包含在程序根目录下的`configuration.json`文件中  

| 配置                      | 说明                   |
| ------------------------- | ---------------------- |
| windows-title             | 程序标题(暂不使用)     |
| background-color          | 背景颜色               |
| font-color                | 候选项字体的颜色       |
| selected-color            | 选中项的颜色           |
| selected-background-color | 选中项的背景色         |
| key-color                 | 左侧输入关键字的颜色   |
| max-key-length            | 最大显示的关键字长度   |
| key-left-margin           | 关键字左外边距         |
| load-software             | 是否加载已安装文件列表 |
| key-font                  | 关键字字体             |
| result-font               | 候选项字体             |
| windows-height | 程序高度 |
| scripts-path | 导入的`python`附属脚本路径(此列表中的所有路径中的`python`脚本都会作为命令导入) |
| lib-path | 导入的外部库(此列表所有路径中的`exe`和`ink`脚本会作为命令导入) |
| scripts-file | 映射配置文件(可以自定义命令) |
| active-hotkey | 激活程序的热键，默认是`alt`+`p` |
| filters | 过滤命令列表，如果你不喜欢已有的一些命令，可以把这些命令名添加进去，导入时会忽略这些命令 |
| rename | 重命名命令 |

### 命令映射  

自定义的命令映射文件默认时程序根目录下的`orders.json`  

**示例**  

```json
{
    "Bili" : "start msedge https://search.bilibili.com/all?keyword=$@"
}
```

这个命令的意思是把`Bili`映射成调用`start msedge`命令并传入`https://search.bilibili.com/all?keyword=$@`这个参数，其中`$@`表示附加的所有信息  

这个命令的意思是打开`bilibili`这个网站并在网站中搜索传入的信息  

*例*  

```
Bili 爬虫
```

则会打开`bilibili`并搜索爬虫相关信息  

# daishan

#### 介绍
岱山项目代码

#### 说明介绍


1.岱山ragflow docker地址：/home/server02/ragflow/docker <br>
在这个路径下跑docker-compose -p ragflow up -d <br>

2.岱山dify调用代码部分 <br>
/home/server02/ai/Digital_human_command_interface/main.py <br>
杀进程命令：lsof -t -i:11029 | xargs kill -9 <br>
启动命令：<br>
nohup python /home/server02/ai/Digital_human_command_interface/main.py >/home/server02/ai/Digital_human_command_interface/main.log 2>&1 &<br>

3.岱山ragflow调用代码部分：<br>
/home/server02/ai/rag_stream/main.py<br>
杀进程命令：lsof -t -i:11027 | xargs kill -9<br>
启动命令：nohup python /home/server02/ai/rag_stream/main.py > /home/server02/ai/rag_stream/main.log 2>&1 &<br>

4.岱山vpn<br>
https://183.245.197.36:4430<br>
账号：yingkeyuan<br>
密码：yky_123<br>

5.岱山ragflow<br>
http://172.16.11.60:8081/knowledge<br>
账号：root@fjkj.com<br>
密码：123456789qwe<br>

6.岱山dify<br>
http://172.16.11.60/apps<br>
账号：root@fjkj.com<br>
密码：123456789qwe<br>

7.岱山达梦数据库信息:<br>
URL: jdbc:dm://172.16.11.73:5236<br>
用户名:parkadmin<br>
密码:Supcon@1304<br>

8.岱山服务器：<br>
1）<br>
Host 岱山服务器<br>
HostName 172.16.11.60<br>
User server82<br>
port 22<br>
/# abc 123<br>
2）<br>
Host 岱山服务器_模型<br>
HostName 172.16.11.61<br>
User server81port 22<br>
/# abc 123<br>

9.岱山模型服务器（61服务器）：<br>
启动命令：(vllm) server01@server01:~/data/model$ nohup sh qwen.sh > output.log 2>&1 &<br>

#### 最近更新（2026-02-25）

1. `rag_stream` 中已补充 `DaiShanSQL` 调用的终端日志输出，统一输出入参/出参提示并控制为单行展示。<br>
2. 已新增与调整相关测试，覆盖关键成功/异常路径，确保日志改造不改变原有业务行为。<br>
3. OpenSpec 变更已完成归档，并同步新增主规范：<br>
   - `openspec/specs/daishansql-terminal-io-logging/spec.md`<br>
   - `openspec/specs/report-function-call-chain/spec.md`<br>

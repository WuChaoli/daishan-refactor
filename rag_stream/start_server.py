#!/usr/bin/env python3
"""
RAG流式回复API服务启动脚本
"""

import uvicorn
import argparse
import sys
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="RAG流式回复API服务")
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="服务监听地址 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="服务监听端口 (默认: 8000)"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1, 
        help="工作进程数 (默认: 1)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="开发模式，自动重载代码"
    )
    parser.add_argument(
        "--log-level", 
        default="info", 
        choices=["debug", "info", "warning", "error"],
        help="日志级别 (默认: info)"
    )
    
    args = parser.parse_args()
    
    # 检查配置文件
    config_file = Path("config.py")
    if not config_file.exists():
        print("错误: 找不到配置文件 config.py")
        sys.exit(1)
    
    # 检查主应用文件
    main_file = Path("main.py")
    if not main_file.exists():
        print("错误: 找不到主应用文件 main.py")
        sys.exit(1)
    
    print("=" * 60)
    print("🚀 RAG流式回复API服务启动中...")
    print("=" * 60)
    print(f"📍 服务地址: http://{args.host}:{args.port}")
    print(f"📚 API文档: http://{args.host}:{args.port}/docs")
    print(f"🔍 健康检查: http://{args.host}:{args.port}/health")
    print(f"👥 工作进程: {args.workers}")
    print(f"🔄 自动重载: {'是' if args.reload else '否'}")
    print(f"📝 日志级别: {args.log_level}")
    print("=" * 60)
    
    try:
        # 启动服务
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            workers=args.workers if not args.reload else 1,
            reload=args.reload,
            log_level=args.log_level,
            access_log=True,
            use_colors=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 服务已停止")
    except Exception as e:
        print(f"\n❌ 服务启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""Mermaid执行路径图生成模块

提供函数调用关系的可视化功能，支持：
- 自动生成调用流程图
- 异常节点标记
- 文件滚动管理
- 线程安全
"""
import os
import time
import threading
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Node:
    """Mermaid节点"""
    id: str
    label: str
    status: str = "success"  # success | error
    timestamp: float = field(default_factory=time.time)


@dataclass
class Edge:
    """Mermaid边"""
    from_id: str
    to_id: str
    is_error: bool = False


class MermaidRecorder:
    """Mermaid图记录器（线程安全）"""

    def __init__(self, entry_func: str, output_dir: str, max_size_mb: int = 10):
        self.entry_func = entry_func
        self.output_dir = output_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._lock = threading.Lock()
        self.nodes: List[Node] = []
        self.edges: List[Edge] = []
        self._parent_stack: List[str] = []  # 父节点栈

    def add_node(self, func_name: str, status: str = "success") -> str:
        """添加节点

        Args:
            func_name: 函数名
            status: 节点状态

        Returns:
            节点ID
        """
        with self._lock:
            timestamp = time.time()
            node_id = f"{func_name}_{int(timestamp * 1000000)}"
            node = Node(id=node_id, label=func_name, status=status, timestamp=timestamp)
            self.nodes.append(node)

            # 如果有父节点，添加边
            if self._parent_stack:
                parent_id = self._parent_stack[-1]
                is_error = (status == "error")
                edge = Edge(from_id=parent_id, to_id=node_id, is_error=is_error)
                self.edges.append(edge)

            # 将当前节点压入父节点栈
            self._parent_stack.append(node_id)

            return node_id

    def mark_error(self, node_id: str):
        """标记节点为错误状态"""
        with self._lock:
            for node in self.nodes:
                if node.id == node_id:
                    node.status = "error"
                    # 更新相关边为错误状态
                    for edge in self.edges:
                        if edge.to_id == node_id:
                            edge.is_error = True
                    break

    def pop_parent(self):
        """弹出父节点（函数返回时调用）"""
        with self._lock:
            if self._parent_stack:
                self._parent_stack.pop()

    def generate_performance_table(self) -> str:
        """生成性能统计表

        Returns:
            Markdown格式的性能统计表
        """
        with self._lock:
            if not self.nodes:
                return ""

            # 表头
            lines = ["## 性能统计", ""]
            lines.append("| 函数名 | 状态 | 时间戳 |")
            lines.append("|--------|------|--------|")

            # 表格内容
            for node in self.nodes:
                status_mark = "❌ ERROR" if node.status == "error" else "✅ SUCCESS"
                timestamp_str = time.strftime("%H:%M:%S", time.localtime(node.timestamp))
                milliseconds = int((node.timestamp % 1) * 1000)
                timestamp_full = f"{timestamp_str}.{milliseconds:03d}"

                lines.append(f"| {node.label} | {status_mark} | {timestamp_full} |")

            lines.append("")
            return "\n".join(lines)

    def generate_ascii_tree(self) -> str:
        """生成ASCII树形结构

        Returns:
            ASCII树形结构字符串
        """
        with self._lock:
            if not self.nodes:
                return ""

            # 构建父子关系映射
            children_map: Dict[str, List[str]] = {}
            for edge in self.edges:
                if edge.from_id not in children_map:
                    children_map[edge.from_id] = []
                children_map[edge.from_id].append(edge.to_id)

            # 找到根节点（没有父节点的节点）
            all_children = set()
            for children in children_map.values():
                all_children.update(children)
            root_nodes = [node.id for node in self.nodes if node.id not in all_children]

            # 如果没有根节点，使用第一个节点
            if not root_nodes:
                root_nodes = [self.nodes[0].id]

            # 生成树形结构
            lines = []
            for root_id in root_nodes:
                self._build_tree_lines(root_id, "", True, lines, children_map)

            return "\n".join(lines)

    def _build_tree_lines(
        self,
        node_id: str,
        prefix: str,
        is_last: bool,
        lines: List[str],
        children_map: Dict[str, List[str]]
    ):
        """递归构建树形结构行

        Args:
            node_id: 当前节点ID
            prefix: 前缀字符串
            is_last: 是否是最后一个子节点
            lines: 输出行列表
            children_map: 父子关系映射
        """
        # 查找节点
        node = None
        for n in self.nodes:
            if n.id == node_id:
                node = n
                break

        if not node:
            return

        # 构建当前行
        connector = "└── " if is_last else "├── "
        error_mark = " [ERROR]" if node.status == "error" else ""
        line = f"{prefix}{connector}{node.label}{error_mark}"
        lines.append(line)

        # 处理子节点
        children = children_map.get(node_id, [])
        for i, child_id in enumerate(children):
            is_last_child = (i == len(children) - 1)
            extension = "    " if is_last else "│   "
            self._build_tree_lines(
                child_id,
                prefix + extension,
                is_last_child,
                lines,
                children_map
            )

    def generate_graph(self) -> str:
        """生成Mermaid flowchart

        Returns:
            Mermaid图字符串
        """
        with self._lock:
            lines = ["flowchart TD"]

            # 生成节点
            for node in self.nodes:
                if node.status == "error":
                    lines.append(f"    {node.id}[{node.label}]:::error")
                else:
                    lines.append(f"    {node.id}[{node.label}]")

            # 生成边
            for edge in self.edges:
                if edge.is_error:
                    lines.append(f"    {edge.from_id} -.-> {edge.to_id}")
                else:
                    lines.append(f"    {edge.from_id} --> {edge.to_id}")

            # 添加错误样式
            lines.append("")
            lines.append("    classDef error fill:#ffcccc,stroke:#ff0000,stroke-width:2px;")

            return "\n".join(lines)

    def save_to_file(self) -> str:
        """保存到Markdown文件并返回文件路径"""
        # 生成各部分内容（不加锁）
        ascii_tree = self.generate_ascii_tree()
        mermaid_graph = self.generate_graph()
        perf_table = self.generate_performance_table()

        with self._lock:
            # 确保目录存在
            full_dir = os.path.join(self.output_dir, self.entry_func)
            os.makedirs(full_dir, exist_ok=True)

            # 检查文件夹大小
            self._cleanup_old_files(full_dir)

            # 生成文件名（改为.md）
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            milliseconds = int((time.time() % 1) * 1000)
            filename = f"{timestamp}.{milliseconds:03d}.md"
            filepath = os.path.join(full_dir, filename)

            # 组合Markdown内容
            content_parts = [
                f"# 执行路径图 - {self.entry_func}",
                "",
                "## ASCII 树形结构",
                "",
                "```",
                ascii_tree,
                "```",
                "",
                perf_table,
                "",
                "## Mermaid 流程图",
                "",
                "```mermaid",
                mermaid_graph,
                "```",
                ""
            ]

            # 写入文件
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(content_parts))

            return filepath

    def _cleanup_old_files(self, directory: str):
        """清理旧文件以控制文件夹大小"""
        if not os.path.exists(directory):
            return

        # 获取所有.md和.mmd文件
        files = []
        for filename in os.listdir(directory):
            if filename.endswith((".md", ".mmd")):
                filepath = os.path.join(directory, filename)
                stat = os.stat(filepath)
                files.append((filepath, stat.st_size, stat.st_mtime))

        # 计算总大小
        total_size = sum(size for _, size, _ in files)

        # 如果超过限制，删除最旧的文件
        if total_size > self.max_size_bytes:
            # 按修改时间排序（旧到新）
            files.sort(key=lambda x: x[2])

            # 删除文件直到大小满足要求
            for filepath, size, _ in files:
                if total_size <= self.max_size_bytes:
                    break
                try:
                    os.remove(filepath)
                    total_size -= size
                except OSError:
                    pass


# 线程本地存储记录器
_recorder_local = threading.local()


def get_current_recorder() -> Optional[MermaidRecorder]:
    """获取当前线程的Mermaid记录器"""
    return getattr(_recorder_local, "recorder", None)


def set_current_recorder(recorder: Optional[MermaidRecorder]):
    """设置当前线程的Mermaid记录器"""
    _recorder_local.recorder = recorder


__all__ = ["MermaidRecorder", "Node", "Edge", "get_current_recorder", "set_current_recorder"]

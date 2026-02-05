# 各语言 LSP 服务器安装配置

本文档提供主流编程语言的 LSP 服务器详细安装命令和配置说明。

---

## 目录

- [Python (Pyright)](#python-pyright)
- [TypeScript/JavaScript (vtsls)](#typescriptjavascript-vtsls)
- [Go (gopls)](#go-gopls)
- [Rust (rust-analyzer)](#rust-rust-analyzer)
- [Java (jdtls)](#java-jdtls)
- [C/C++ (clangd)](#cc-clangd)
- [C# (OmniSharp)](#c-omnisharp)
- [PHP (Phpactor)](#php-phpactor)
- [Kotlin (kotlin-lsp)](#kotlin-kotlin-lsp)
- [Ruby (ruby-lsp)](#ruby-ruby-lsp)
- [HTML/CSS/JSON (vscode-langservers)](#htmlcssjson-vscode-langservers)

---

## Python (Pyright)

Pyright 提供强大的类型检查和快速性能,适合带类型提示的项目。

### 安装

```bash
# npm
npm install -g pyright

# pnpm
pnpm install -g pyright

# bun
bun install -g pyright
```

### 配置

Pyright 会读取 `pyrightconfig.json` 或 `pyproject.toml`:

```json
// pyrightconfig.json
{
  "include": ["src"],
  "exclude": ["**/node_modules"],
  "venvPath": ".",
  "venv": ".venv"
}
```

或在 `pyproject.toml` 中:

```toml
[tool.pyright]
include = ["src"]
exclude = ["**/node_modules"]
venvPath = "."
venv = ".venv"
```

### 验证

```bash
which pyright
# 应返回安装路径
```

---

## TypeScript/JavaScript (vtsls)

vtsls 提供完整的 TypeScript/JavaScript 支持,包括 JSDoc 注释解析。

### 安装

```bash
# npm
npm install -g @vtsls/language-server typescript

# pnpm
pnpm install -g @vtsls/language-server typescript

# bun
bun install -g @vtsls/language-server typescript
```

**重要:** TypeScript 必须一起安装,否则类型可能无法正确解析。

### 配置

vtsls 通常无需额外配置,会自动读取项目中的 `tsconfig.json`。

### 验证

```bash
which vtsls
which tsc
```

---

## Go (gopls)

Google 官方的 Go 语言服务器,对 Go 模块和工作区支持完整。

### 安装

```bash
go install golang.org/x/tools/gopls@latest
```

### 配置

确保 `$GOPATH/bin` 在 PATH 中:

```bash
export PATH=$PATH:$(go env GOPATH)/bin
```

添加到 `~/.zshrc` 或 `~/.bashrc` 使其永久生效。

### 验证

```bash
which gopls
# 应返回 $GOPATH/bin/gopls 或类似路径
```

---

## Rust (rust-analyzer)

与 Cargo 和 Rust 生态系统深度集成的语言服务器。

### 安装

```bash
rustup component add rust-analyzer
```

### 配置

rust-analyzer 会自动读取 `Cargo.toml` 并处理工作区依赖,通常无需额外配置。

### 验证

```bash
which rust-analyzer
# 应返回安装路径
```

---

## Java (jdtls)

Eclipse JDT 语言服务器,提供完整的 Java 支持。

### 系统要求

Java 21 或更高版本

### 安装

```bash
# 下载最新版本
curl -LO http://download.eclipse.org/jdtls/snapshots/jdt-language-server-latest.tar.gz

# 解压到本地目录
mkdir -p ~/jdtls
tar -xzf jdt-language-server-latest.tar.gz -C ~/jdtls
```

或通过包管理器:

```bash
# macOS
brew install jdtls
```

### 配置

大型 Java 项目可能需要增加可用 RAM 以保证性能。

### 验证

```bash
which jdtls
```

---

## C/C++ (clangd)

提供快速索引和良好性能的 C/C++ 语言服务器。

### 安装

```bash
# macOS
brew install llvm

# Ubuntu/Debian
sudo apt-get install clangd

# Arch Linux
sudo pacman -S clang
```

或从 [LLVM 官方发布页面](https://github.com/clangd/clangd/releases) 下载。

### 配置

对于复杂项目,需要生成 `compile_commands.json`:

```bash
# 使用 cmake
cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=1 ..

# 使用 Bear
bear make
```

### 验证

```bash
which clangd
```

---

## C# (OmniSharp)

为 .NET 和 C# 开发提供全面支持。

### 安装

```bash
# macOS
brew install omnisharp/omnisharp-roslyn/omnisharp-mono
```

或从 [官方发布](https://github.com/OmniSharp/omnisharp-roslyn/releases) 下载:

```bash
# Linux/macOS
curl -L https://github.com/OmniSharp/omnisharp-roslyn/releases/latest/download/omnisharp-linux-x64-net6.0.tar.gz | tar xz -C ~/.local/bin
```

### 配置

确保 OmniSharp 可执行文件在 PATH 中。

### 验证

```bash
which OmniSharp
```

---

## PHP (Phpactor)

提供快速而强大的智能提示。

### 安装

```bash
# 通过 Composer (推荐)
composer global require phpactor/phpactor

# 或通过包管理器
# macOS
brew install phpactor/tap/phpactor
```

### 配置

确保 Composer vendor bin 在 PATH 中:

```bash
export PATH=$PATH:~/.composer/vendor/bin
# 或
export PATH=$PATH:~/.config/composer/vendor/bin
```

### 验证

```bash
which phpactor
```

---

## Kotlin (kotlin-lsp)

Kotlin 语言支持。

### 系统要求

Java 17 或更高版本

### 安装

```bash
# macOS
brew install JetBrains/utils/kotlin-lsp
```

或从官方 releases 下载,将可执行文件添加到 PATH。

### 限制

目前只支持基于 JVM 的 Kotlin Gradle 项目。

### 验证

```bash
which kotlin-lsp
```

---

## Ruby (ruby-lsp)

Ruby 语言服务器支持。

### 安装

```bash
gem install ruby-lsp
```

### 配置

在项目中,确保 Gemfile 包含:

```ruby
group :development do
  gem "ruby-lsp", require: false
end
```

然后运行:

```bash
bundle install
```

### 验证

```bash
which ruby-lsp
```

---

## HTML/CSS/JSON (vscode-langservers)

为 Web 技术提供 LSP 支持。

### 安装

```bash
# npm
npm install -g vscode-langservers-extracted

# pnpm
pnpm install -g vscode-langservers-extracted

# bun
bun install -g vscode-langservers-extracted
```

### 支持的语言

- HTML
- CSS
- JSON
- JavaScript (部分支持)

### 验证

```bash
which vscode-html-language-server
which vscode-css-language-server
which vscode-json-language-server
```

---

## 通用验证步骤

所有语言服务器安装后,请验证:

1. **二进制文件在 PATH 中**

   ```bash
   which [language-server-name]
   ```

2. **在 Claude Code 中检查插件状态**

   ```
   /plugin
   # 查看 "Installed" 标签
   ```

3. **测试 LSP 功能**

   ```
   > 跳转到 [某个函数] 的定义
   # 应返回精确位置,而非搜索结果
   ```

## 配置文件位置

不同语言的配置文件:

| 语言 | 配置文件 |
|------|----------|
| Python | `pyrightconfig.json`, `pyproject.toml` |
| TypeScript | `tsconfig.json` |
| Go | `go.mod` |
| Rust | `Cargo.toml` |
| Java | `.classpath`, `.project` |
| C/C++ | `compile_commands.json` |
| C# | `.sln`, `.csproj` |
| Ruby | `Gemfile` |

## 多语言项目

在多语言项目中:

1. 为每种语言安装对应的 LSP 服务器
2. Claude Code 根据文件扩展名自动切换
3. 无需手动配置,插件会自动激活

例如,一个包含 Python 后端和 TypeScript 前端的项目会同时使用 Pyright 和 vtsls。

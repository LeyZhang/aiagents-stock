# 使用官方Python镜像作为基础镜像
FROM python:3.12-slim

# 设置时区环境变量
ENV TZ=Asia/Shanghai

# 替换apt-get源为国内源（清华源）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true

# 创建vscode用户
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

RUN export USERNAME=${USERNAME:-vscode} \
    && export USER_UID=${USER_UID:-1000} \
    && export USER_GID=${USER_GID:-1000} \
    && groupadd --gid $USER_GID $USERNAME 2>/dev/null || groupadd --gid $USER_GID $USERNAME || true \
    && useradd --uid $USER_UID --gid $USER_GID --shell /bin/bash --create-home $USERNAME 2>/dev/null || useradd --uid $USER_UID --gid $USER_GID --shell /bin/bash --create-home $USERNAME || true \
    && mkdir -p /etc/sudoers.d \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# 设置工作目录
WORKDIR /workspaces/aiagents-stock

# 安装Homebrew需要的依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tar \
    xz-utils \
    ca-certificates \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fontconfig \
    tzdata \
    wget \
    git \
    vim \
    build-essential \
    procps \
    sudo \
    bash \
    file \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER $USERNAME
ENV HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git" \
    HOMEBREW_CORE_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git" \
    HOMEBREW_BOTTLE_DOMAIN="https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles" \
    HOMEBREW_API_DOMAIN="https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles/api"
RUN /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
ENV PATH="/home/linuxbrew/.linuxbrew/bin:${PATH}"
ENV git config --global --add safe.directory /home/linuxbrew/.linuxbrew/Homebrew
ENV brew update && brew install opencode && brew install oven-sh/bun/bun
ENV bunx oh-my-opencode install --no-tui --claude=no --chatgpt=no --gemini=no

USER root
# 配置pip使用清华源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 复制依赖文件并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p /workspaces/aiagents-stock/data && \
    chmod 777 /workspaces/aiagents-stock/data && \
    chown -R $USERNAME:$USERNAME /workspaces/aiagents-stock

# 暴露Streamlit默认端口
EXPOSE 8503

# 设置健康检查
HEALTHCHECK CMD python -c "import streamlit; streamlit.run('/workspaces/aiagents-stock/app.py', daemon=True)" 2>/dev/null || curl --fail http://localhost:8503/_stcore/health || exit 1

# 默认命令
CMD ["streamlit", "run", "app.py", "--server.port=8503", "--server.address=0.0.0.0"]

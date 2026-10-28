FROM python:3.11-slim

WORKDIR /workspaces

RUN python -m pip install --upgrade pip && \
    python -m pip install numpy matplotlib seaborn scipy

ENV MPLBACKEND=Agg

CMD ["bash"]

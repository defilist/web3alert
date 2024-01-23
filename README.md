# Web3 Alert

## Requirements

1. Run OpenSearch

Ref [Install OpenSearch](https://opensearch.org/docs/latest/install-and-configure/install-opensearch/index/) for more detail

hint: if you are running in macOS, use `brew install opensearch` instead.

eg: run in docker

```bash
docker run -d -p 9200:9200 -p 9600:9600 --name opensearch -e "discovery.type=single-node" -e "plugins.security.disabled=true" opensearchproject/opensearch:2
```

2. Run OpenSearch-Dashboards 2.6.0

```bash
git clone --branch 2.6.0 --single-branch https://github.com/opensearch-project/OpenSearch-Dashboards
```

3. Install the [web3_soc](./web3_soc) plugin into OpenSearch

```bash
cp -r web3_soc /path/to/OpenSearch-Dashboards/plugins/
```

4. Run Opensearch-Dashboards

```bash
cd /path/to/OpenSearch-Dashboards/
cat <<EOF > opensearch_dashboards.yml
opensearch.hosts: ["http://127.0.0.1:9200"]
opensearch.username: "admin"
opensearch.password: "admin"
opensearch.ssl.verificationMode: none
EOF
```

Start Opensearch-Dashboards

```bash
yarn
yarn osd bootstrap
yarn start
```

4. Run [api](./api.py) and [etl](./etl.py) in docker-compose

```bash
cp .env.example .env

docker-compose -f prod.docker-compose.yaml
```

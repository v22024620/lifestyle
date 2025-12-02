# Protege Setup for LOP Ontology

1. **Raw 모듈 위치 지정**
   - `git clone https://github.com/edmcouncil/fibo.git fibo-master` (이미 존재하면 최신 태그로 업데이트)
   - `python data/ontology/pipelines/sync_fibo_modules.py --clean` 실행 → `data/ontology/raw/`에 필요한 FIBO 모듈과 `catalog-v001.xml`이 복사됩니다.

2. **Protege catalog 설정**
   - Protege 실행 후 `File > Preferences > XML Catalogs` 메뉴에서 `Add...`를 선택하고 `data/ontology/raw/metadata/catalog-v001.xml` 경로를 추가합니다.
   - catalog 엔트리 내 `uri`를 `https://spec.edmcouncil.org/fibo/ontology`로 유지하면 Protege가 `raw/FND/*` 등 로컬 경로를 해석합니다.

3. **프로젝트 로딩 순서**
   - `File > Open...`으로 `data/ontology/lop/LOP-Metadata.ttl`을 엽니다.
   - Protege가 `owl:imports`를 통해 `lop/LOP-Core.ttl`을 자동으로 가져오고, Raw 계층의 FIBO 모듈도 catalog 경로로 불러옵니다.

4. **Reasoner 검증**
   - Reasoner를 `HermiT` 또는 `ELK`로 선택 후 `Start reasoner`를 클릭합니다.
   - 무결성 검증 후 필요한 주석/정의를 Protege에서 수정하고 저장합니다.

5. **내보내기**
   - 변경 사항은 `lop/*.ttl`에 저장되므로 Git으로 커밋하면 GraphDB/Neo4j 파이프라인에서도 동일한 결과를 사용할 수 있습니다.

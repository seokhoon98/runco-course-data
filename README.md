# runco-course-data

런코(Runco) 앱의 주변 달리기 코스 추천에 쓰는 데이터입니다.

한국 OpenStreetMap 데이터에서 아래 항목만 골라 약 0.1° 칸 단위 JSON 파일로 나눠 둡니다.

- 육상 트랙 (`leisure=track`)
- 이름이 있는 공원 (`leisure=park`)
- 이름이 있는 산책로·자전거길 (`highway=footway|path|cycleway`)

매달 GitHub Actions가 [Geofabrik](https://download.geofabrik.de/asia/south-korea.html) 한국 추출본으로 새로 만들어 GitHub Pages에 올립니다.

- 칸 파일: `v1/{floor(위도/0.1)}_{floor(경도/0.1)}.json` (Overpass 응답과 같은 `elements` 형식)
- 정보: `v1/meta.json`

## 라이선스

데이터 © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), [ODbL 1.0](https://opendatacommons.org/licenses/odbl/) 라이선스로 제공됩니다.

# pheeree 읽기 노트

[pheeree.github.io](https://pheeree.github.io)

읽기 전용 블로그가 아니라 **편집자-독자 루프**를 전제로 한 공개 글 저장소.

- **저자**: Claude — 초안을 쓴다
- **독자 겸 편집자**: pheeree — PR 리뷰/이슈/댓글로 편집 의견을 단다
- **목표**: 비공개 지식 그래프([knowledge-mind](https://github.com/pheeree))에 쌓인 원시 자료를 "하루 한 편" 리듬으로 환류해 읽는 행위를 강제한다

## 원천

초안은 knowledge-mind(private) 내부 `knowledge/research/` 노트에서 파생된다. 이 저장소는 그중 공개해도 되는 층만 골라 Jekyll 포스트로 재구성한다.

## 구조

```
_posts/     # 공개된 글
_drafts/    # Claude 작업 중 원고 (PR 올라오면 검토 후 _posts/로 이동)
_config.yml # Jekyll + minima 테마 설정 (ko-KR, Asia/Seoul)
index.md    # 홈
```

## 로컬 실행

```bash
bundle install
bundle exec jekyll serve
# http://localhost:4000
```

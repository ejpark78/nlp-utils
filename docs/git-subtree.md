
# git subtree

## subtree 등록 

```bash
# git remote add { Remote name } { Child repo }
# git subtree add --prefix { Child path } { Remote name } { Child branch }

git remote add config http://galadriel02.korea.ncsoft.corp/crawler-dev/config.git
git subtree add --prefix config config dev

git remote add helm http://galadriel02.korea.ncsoft.corp/crawler-dev/helm.git
git subtree add --prefix helm helm dev

git remote add dags http://galadriel02.korea.ncsoft.corp/crawler-dev/dags.git
git subtree add --prefix dags dags dev

git remote add http http://galadriel02.korea.ncsoft.corp/crawler-dev/http.git
git subtree add --prefix http http dev

git remote add docker http://galadriel02.korea.ncsoft.corp/crawler-dev/docker.git
git subtree add --prefix docker docker dev

git remote -v
```

## parent 저장소 관리 

**이렇게 git push만 하는 경우에는 오로지 Parent 저장소에만 Child의 변경 사항이 반영됩니다.**

```bash
git add { Child path }
git commit -m { Commit message }
git push origin { branch }
```

## child 저장소 관리 

**Parent에서 Child 변경 사항을 Child 저장소에도 반영하기 위해선 이 기능을 사용해야 합니다.**

```bash
# push
git subtree push --prefix { Child path } { Remote name } { Child branch }

# pull
git subtree pull --prefix { Child path } { Remote name } { Child branch }
```

# ref

* [Git Subtree 사용법 - 하나의 저장소에서 여러 저장소를 관리하기](https://iseongho.github.io/posts/git-subtree/)
* [Git subtree: the alternative to Git submodule](https://www.atlassian.com/git/tutorials/git-subtree)
  ![img](https://wac-cdn.atlassian.com/dam/jcr:f5fcef58-5b93-4ff4-b9a1-3f721d29ead8/BeforeAfterGitSubtreeDiagram.png?cdnVersion=1535)
* [Git subtree를 활용한 코드 공유](https://blog.rhostem.com/posts/2020-01-03-code-sharing-with-git-subtree)
* [[Git] Subtree 사용법](https://www.three-snakes.com/git/git-subtree)

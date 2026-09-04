# 구성 증빙 (콘솔 캡처)

운영 중이던 환경에서 직접 찍은 AWS 콘솔 화면입니다. 저장소의 설정 파일이 실제로 어떤 리소스를 만들었는지 대조할 수 있습니다.

**계정 ID와 IAM 사용자 이름은 잘라내거나 가렸습니다.** 여러 사람이 함께 쓰던 교육 계정이라 계정 소유자를 식별할 수 있는 정보만 제거했고, 리소스 ID는 남겼습니다 — 리소스 ID는 계정 접근 권한 없이는 아무 의미가 없고, 저장소의 설정 파일과 대조하려면 필요합니다. 해당 리소스는 전부 삭제된 상태입니다.

| 화면 | 무엇을 보면 되는지 | 관련 파일 |
|---|---|---|
| [`subnets.png`](subnets.png) | 3AZ × 3계층 = 9개. **퍼블릭 3개만 「퍼블릭 IPv4 자동 할당 = 예」** 이고 라우팅 테이블도 계층별로 나뉜다 | [`q10/cluster.yaml`](../../q10/cluster.yaml) |
| [`instances.png`](instances.png) | 앱 인스턴스와 EKS 노드는 **퍼블릭 IP 칸이 비어 있다**(프라이빗). Bastion만 공인 IP를 가진다 | [`q4/userdata.sh`](../../q4/userdata.sh) |
| [`loadbalancers.png`](loadbalancers.png) | ALB 2개가 **같은 VPC**에 있다. 네트워크가 갈라져서가 아니라 대상 유형 때문에 2개다 | [`q11/k8s/04-nginx-ingress.yaml`](../../q11/k8s/04-nginx-ingress.yaml) |
| [`target-groups.png`](target-groups.png) | `대상 유형` 이 하나는 **IP**(파드), 하나는 **인스턴스**(EC2). 파드 IP는 계속 바뀌므로 하나로 합칠 수 없다 | 〃 |
| [`target-group-detail.png`](target-group-detail.png) | 헬스체크 수정 후 등록 대상 1개 `Healthy`. 이 Healthy 는 nginx만이 아니라 fastAPI·MySQL까지 살아 있다는 뜻이다 | [`q4/nginx/default.conf`](../../q4/nginx/default.conf) |
| [`autoscaling-group.png`](autoscaling-group.png) | 원하는 용량 1 / 한도 1\~2, 프라이빗 서브넷 3개. 시작 템플릿 설명이 `nginx+fastapi+mysql compose from S3` | [`q4/docker-compose.yaml`](../../q4/docker-compose.yaml) |
| [`rds-proxy.png`](rds-proxy.png) | 상태 **사용 가능**, IAM 역할 지정, 프라이빗 서브넷 3개 | [`q9/lambda-student.py`](../../q9/lambda-student.py) |
| [`eks-cluster.png`](eks-cluster.png) | 1.34 · 클러스터 문제 0 · 노드 상태 문제 0. **OpenID Connect 공급자 URL** 이 IRSA 구성의 근거 | [`q10/cluster.yaml`](../../q10/cluster.yaml) |
| [`security-groups.png`](security-groups.png) | 직접 지정한 5개와 EKS가 자동 생성한 5개. 설명 열에 용도를 적어 두었다 | — |
| [`security-group-db-inbound.png`](security-group-db-inbound.png) | 인바운드 5개가 전부 **IP가 아닌 보안 그룹 참조**이고, 마지막 줄이 **자기 자신 참조**다 | — |
| [`api-gateway-routes-1.png`](api-gateway-routes-1.png) | 사이트 진입 경로. `/docker` 아래 `/{proxy+}` 가 상대경로 링크를 받아내는 캐치올 | — |
| [`api-gateway-routes-2.png`](api-gateway-routes-2.png) | API 경로. `/student/list`→Lambda, `/loadlist/{proxy+}`→EC2 ALB, `/test`·`/score`→EKS ALB | [`q11/k8s/04-nginx-ingress.yaml`](../../q11/k8s/04-nginx-ingress.yaml) |

## 보안 그룹 자기 참조

`security-group-db-inbound.png` 의 마지막 줄이 이 프로젝트에서 두 번 발목을 잡은 부분입니다.

**보안 그룹은 같은 그룹에 속한 리소스끼리도 자동으로 통신을 허용하지 않습니다.** RDS Proxy와 DB를 둘 다 `db-sg` 에 넣었는데 3306 인바운드에 자기 참조가 없어 프록시가 `UNAVAILABLE` 에서 벗어나지 못했습니다. 콘솔 메시지는 `DBProxy Target is waiting for proxy to scale to desired capacity` 라 용량 문제처럼 읽혀서 원인을 찾는 데 시간이 걸렸습니다. 같은 함정이 EKS 노드 SG에서 한 번 더 반복됐습니다.

인바운드를 전부 **IP가 아닌 보안 그룹 참조**로 구성한 것도 이 때문입니다. ASG가 인스턴스를 교체하거나 파드 IP가 바뀌어도 규칙을 고칠 필요가 없습니다.

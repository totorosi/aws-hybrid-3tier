이 폴더의 JSON 은 쿠버네티스 매니페스트가 아니라 AWS IAM 정책 문서다.
kubectl 이 아니라 aws iam create-policy 의 입력으로 쓴다.

  alb-iam-policy.json
    출처: AWS Load Balancer Controller 프로젝트 배포본
    만든 정책: std15-test-alb-controller-policy
    용도: Ingress 를 보고 ALB / 리스너 / 타겟그룹을 대신 만들 권한

  eso-iam-policy.json
    출처: 직접 작성
    만든 정책: std15-test-eso-policy
    용도: External Secrets Operator 가 Secrets Manager 를 읽을 권한
          (secretsmanager:GetSecretValue + kms:Decrypt)

실행한 명령:
  aws iam create-policy --policy-name std15-test-alb-controller-policy \
      --policy-document file://alb-iam-policy.json
  aws iam create-policy --policy-name std15-test-eso-policy \
      --policy-document file://eso-iam-policy.json

이 정책들은 eksctl create iamserviceaccount 로 IRSA 역할에 연결된다.
  std15-test-alb-controller-role  <- kube-system/aws-load-balancer-controller
  std15-test-eso-role             <- external-secrets/external-secrets

resource "aws_ecs_cluster" "main" {
  name = "rag-cluster"
}

resource "aws_ecs_task_definition" "rag" {
  family                   = "rag-project"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([{
    name  = "rag-project"
    image = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/rag-project:latest"
    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]
    secrets = [
      { name = "ANTHROPIC_API_KEY",  valueFrom = "${aws_secretsmanager_secret.rag_env.arn}:ANTHROPIC_API_KEY::" },
      { name = "PINECONE_API_KEY",   valueFrom = "${aws_secretsmanager_secret.rag_env.arn}:PINECONE_API_KEY::" },
      { name = "PINECONE_INDEX_NAME", valueFrom = "${aws_secretsmanager_secret.rag_env.arn}:PINECONE_INDEX_NAME::" },
      { name = "S3_BUCKET_NAME",     valueFrom = "${aws_secretsmanager_secret.rag_env.arn}:S3_BUCKET_NAME::" }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = "/ecs/rag-project"
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "ecs"
      }
    }
  }])
}

resource "aws_ecs_service" "rag" {
  name            = "rag-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.rag.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = ["subnet-07ba9e0a8f0a7fc59"]
    security_groups  = ["sg-04b86ec03923ddbce"]
    assign_public_ip = true
  }
}
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { ValidationPipe } from '@nestjs/common';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import cors from 'cors';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const corsMiddleware = (
    cors as unknown as () => import('express').RequestHandler
  )();
  app.use(corsMiddleware);
  app.useGlobalPipes(new ValidationPipe());
  app.setGlobalPrefix('api');

  // 初始化 Swagger / OpenAPI 规范
  const config = new DocumentBuilder()
    .setTitle('Alpha Agent API')
    .setDescription('Alpha Agent RAG 后端服务 API 文档，可直接导入 ApiFox')
    .setVersion('1.0')
    .addTag('Agent RAG')
    .build();

  const documentFactory = () => SwaggerModule.createDocument(app, config);
  // 通过 /api-docs 路径暴露 Swagger UI
  SwaggerModule.setup('api-docs', app, documentFactory);

  await app.listen(3000);
  console.log('✅ AlphaAgent Backend running on http://localhost:3000');
  console.log('📖 Swagger 文档已运行在 http://localhost:3000/api-docs');
  console.log('🔗 ApiFox JSON 导入地址: http://localhost:3000/api-docs-json');
}
void bootstrap();

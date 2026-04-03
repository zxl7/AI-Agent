import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsArray, IsOptional, IsString } from 'class-validator';

export class AddVectorDto {
  @ApiProperty({
    description: '要存入知识库的文本段落数组',
    example: ['Alpha Agent 的核心代号是 Project X'],
    type: [String],
  })
  @IsArray()
  @IsString({ each: true })
  texts: string[];

  @ApiPropertyOptional({
    description: '每段文本对应的元数据，用于后续过滤（可选）',
    example: [{ category: 'project_info' }],
    type: [Object],
  })
  @IsOptional()
  @IsArray()
  metadatas?: Record<string, any>[];
}

export class ChatDto {
  @ApiProperty({
    description: '用户提出的问题',
    example: '你知道 Alpha Agent 的核心代号是什么吗？',
    type: String,
  })
  @IsString()
  question: string;
}

import { Module } from '@nestjs/common';
import { LlmService } from './llm.service';

/**
 * 本地大模型模块
 */
@Module({
  providers: [LlmService],
  exports: [LlmService],
})
export class LlmModule {}

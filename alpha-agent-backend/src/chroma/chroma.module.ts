import { Module } from '@nestjs/common';
import { ChromaService } from './chroma.service';

/**
 * Chroma 模块
 * 负责提供 ChromaDB 相关的功能服务
 */
@Module({
  providers: [ChromaService],
  exports: [ChromaService],
})
export class ChromaModule {}

import { Module } from '@nestjs/common';
import { ChromaService } from './chroma.service';
import { VectorService } from './vector.service';

/**
 * Chroma 模块
 * 负责提供 ChromaDB 相关的功能服务
 */
@Module({
  providers: [ChromaService, VectorService],
  exports: [ChromaService, VectorService],
})
export class ChromaModule {}

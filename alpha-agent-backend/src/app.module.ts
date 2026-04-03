import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ChromaModule } from './chroma/chroma.module';
import { LlmModule } from './llm/llm.module';

@Module({
  imports: [ChromaModule, LlmModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}

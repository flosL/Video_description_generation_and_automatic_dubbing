import torch
import torch.nn as nn
import os
from typing import List, Optional, Tuple, Dict
from transformers import AutoTokenizer


class CapPreprocessor:
    def __init__(self, tokenizer_type, device=torch.device('cuda'), tokenizer_path=None):
        self.tokenizer_type = tokenizer_type
        self.device = device

        # 优先使用本地路径加载tokenizer，如果没有提供则尝试从网上下载
        try:
            if tokenizer_path and os.path.exists(tokenizer_path):
                print(f"从本地路径加载tokenizer: {tokenizer_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
            else:
                print(f"尝试从预训练模型加载tokenizer: {tokenizer_type}")
                self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_type)
            self.pad_id = self.tokenizer.convert_tokens_to_ids("[PAD]")
            self.start_id = self.tokenizer.convert_tokens_to_ids("[CLS]")
            self.end_id = self.tokenizer.convert_tokens_to_ids("[SEP]")
        except Exception as e:
            print(f"加载tokenizer失败: {e}")
            print("将使用简单的分词器作为替代")
            # 创建一个简单的分词器作为替代
            self._create_simple_tokenizer()

    def __call__(self, captions: List[str]) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Turn raw text captions to tensor by Hugging Face tokenizer
        text -> id -> batching -> masking
        :param captions: list of raw caption strings.
        :return: batched text tensor and mask tensor (True for valid position).
        """
        # 1-pass
        batch_size = len(captions)
        tokens = []
        for i in range(batch_size):
            tokens.append(self.tokenizer.encode(captions[i], return_tensors="pt").squeeze().to(self.device))
        # 2-pass
        text_len = [len(i) for i in tokens]
        max_len = max(text_len)
        text_ts = torch.ones([batch_size, max_len], dtype=torch.long).to(self.device) * self.pad_id
        for i in range(batch_size):
            text_ts[i, :len(tokens[i])] = tokens[i]
        text_mask_ts = (text_ts == self.pad_id).to(self.device)
        return text_ts, text_mask_ts
    
    def _create_simple_tokenizer(self):
        """
        创建一个简单的分词器作为替代
        """
        # 定义简单的词表
        self.vocab = {
            '[PAD]': 0,
            '[CLS]': 1,
            '[SEP]': 2,
            '[UNK]': 3,
            # 常见词
            'a': 4, 'the': 5, 'is': 6, 'are': 7, 'and': 8, 'or': 9, 'of': 10, 'in': 11,
            'on': 12, 'at': 13, 'to': 14, 'for': 15, 'with': 16, 'by': 17, 'from': 18,
            # 常见名词
            'person': 19, 'man': 20, 'woman': 21, 'child': 22, 'people': 23,
            'hand': 24, 'face': 25, 'head': 26, 'body': 27,
            # 常见动词
            'doing': 28, 'using': 29, 'holding': 30, 'sitting': 31, 'standing': 32,
            'walking': 33, 'running': 34, 'playing': 35, 'talking': 36,
            # 常见形容词
            'red': 37, 'blue': 38, 'green': 39, 'yellow': 40, 'white': 41, 'black': 42,
            # 常见数字
            '1': 43, '2': 44, '3': 45, '4': 46, '5': 47
        }
        
        # 设置特殊token的ID
        self.pad_id = self.vocab['[PAD]']
        self.start_id = self.vocab['[CLS]']
        self.end_id = self.vocab['[SEP]']
        self.unk_id = self.vocab['[UNK]']
        
        # 创建简单的tokenizer类
        class SimpleTokenizer:
            def __init__(self, vocab, unk_id):
                self.vocab = vocab
                self.unk_id = unk_id
                self.vocab_size = len(vocab)
            
            def encode(self, text, return_tensors=None):
                # 简单分词: 转小写，按空格分割
                words = text.lower().split()
                # 添加开始和结束标记
                ids = [vocab['[CLS]']] + [self.vocab.get(word, self.unk_id) for word in words] + [vocab['[SEP]']]
                # 如果需要返回tensor
                if return_tensors == 'pt':
                    return torch.tensor([ids])
                return ids
            
            def convert_tokens_to_ids(self, token):
                return self.vocab.get(token, self.unk_id)
        
        # 实例化简单分词器
        self.tokenizer = SimpleTokenizer(self.vocab, self.unk_id)
        print(f"简单分词器已创建，词汇表大小: {len(self.vocab)}")





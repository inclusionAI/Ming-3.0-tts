import re
import string
import unicodedata

def is_chinese(text):
    """检测文本是否包含中文"""
    # 使用简单规则判断
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def get_lang_type(text):
    """
    - 'zh': 只包含中文字符（及相关标点）。
    - 'en': 只包含英文字符（及相关标点）。
    - 'mixed': 同时包含中文字符和英文字符。
    - 'other': 只包含数字、符号等，不含中英文字符。
    """
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    has_english = bool(re.search(r'[a-zA-Z]', text))

    if has_chinese and has_english:
        return 'mixed'
    if has_chinese:
        return 'zh'
    if has_english:
        return 'en'
    return 'other'

    
def split_and_group_sentences(text, group_by_lang=False):
    # 分句正则表达式，匹配中文和英文的句子结束标点
    # pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=[.!?。！？])\s*'
    # 仅匹配中文冒号 `：` 或英文冒号 `:` 后跟空格的情况
    pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=[.!?。！？]|:(?=\s)|：)\s*'
    sentences = [s.strip() for s in re.split(pattern, text.strip()) if s.strip()]
    
    if not group_by_lang:
        return sentences
    
    # 聚合相同语言的相邻子句
    grouped = []
    current_group = []
    current_lang = None
    
    for sentence in sentences:
        lang = 'zh' if is_chinese(sentence) else 'en'
        
        if current_lang is None:
            current_group.append(sentence)
            current_lang = lang
        elif lang == current_lang:
            # 中文直接连接，英文添加空格
            if lang == 'zh':
                current_group.append(sentence)
            else:
                current_group.append(' ' + sentence if sentence[0].isalnum() else sentence)
        else:
            grouped.append(''.join(current_group))
            current_group = [sentence]
            current_lang = lang
    
    if current_group:
        grouped.append(''.join(current_group))
    
    return grouped


def get_semantic_length(text):
    """
    计算字符串的语义长度。
    一个汉字、日文假名或韩文音节计为1，一个拉丁字母词计为1。
    拉丁词支持重音字母和词内撇号，例如 mañana 和 don't 均计为1。
    """
    text = unicodedata.normalize('NFC', text)
    cjk_char_count = len(re.findall(
        r'[\u4e00-\u9fff\u3041-\u3096\u309d-\u309f'
        r'\u30a1-\u30fa\u30fc-\u30ff\uac00-\ud7a3]', text))
    latin_letters = r'A-Za-z\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u024f\u1e00-\u1eff'
    latin_word_count = len(re.findall(
        rf'[{latin_letters}]+(?:[\'’][{latin_letters}]+)*', text))
    return cjk_char_count + latin_word_count
    
def has_valid_content(text):
    """
    判断文本是否包含有效字符（非标点符号）
    """
    punctuation_and_whitespace = string.punctuation + string.whitespace
    for char in text:
        if char not in punctuation_and_whitespace:
            return True
    return False
    
def append_text_fragment(fragments, new_text, max_len, min_tail_length):
    """
    将新文本追加到片段列表中，根据语义长度决定是否合并
    """
    # 清理 new_text 的前导标点和空格
    new_text = new_text.lstrip("，,:;" + string.whitespace)
    if not has_valid_content(new_text):
        return fragments 

    if not fragments:
        fragments.append(new_text)
        return fragments

    last_fragment = fragments[-1]
    last_semantic_len = get_semantic_length(last_fragment)
    new_semantic_len = get_semantic_length(new_text)

    if last_semantic_len + new_semantic_len <= max_len:
        # 特殊处理：如果上一段以句号结尾且新文本很短，则开启新段落
        if last_fragment.endswith(("。", "！", "？")) and new_semantic_len < min_tail_length:
            fragments.append(new_text)
        else:
            # 决定连接符，让中英文拼接更自然
            separator = ""
            # 如果上一个片段结尾不是空格，且新片段以英文/数字开头，则加个空格
            if not last_fragment.endswith(" ") and re.match(r'^[a-zA-Z0-9]', new_text):
                 separator = " "
            fragments[-1] += separator + new_text
    else:
        # 开启新段落时，new_text 已经被清理过了
        fragments.append(new_text)
    return fragments


def split_long_fragment(text_fragment, max_len):
    """
    沿标点边界分割超长片段。max_len 是聚合目标，无标点的完整子句
    即使超过目标也整体保留，不按字或词强制截断。
    """
    fragment_semantic_len = get_semantic_length(text_fragment)
    if fragment_semantic_len <= max_len:
        return [text_fragment]

    # —— 第一优先级:沿标点切 clause ——
    # 标点(中文，、；。！？ + 英文 ,;!?!) 及列表分隔(空格+[-•·]) 作为切分边界。
    # 用 split 保留分隔符并并回前一 clause, 使子串拼接 == 原文(位置校准仍能 find 到)。
    clause_pattern = r'([，、；。！？,;!?]|\s+[-•·])'
    parts = re.split(clause_pattern, text_fragment)
    merged_clauses = []
    for part in parts:
        if part == "":
            continue
        if merged_clauses and re.fullmatch(clause_pattern, part):
            merged_clauses[-1] += part          # 标点/分隔 并回前一段
        else:
            merged_clauses.append(part)

    fragments = []
    current_fragment = ""

    for clause in merged_clauses:
        clause_semantic_len = get_semantic_length(clause)

        # 超长子句整体保留，避免将词语或没有标点的语义单元拆开。
        if clause_semantic_len > max_len:
            if current_fragment:
                fragments.append(current_fragment)
                current_fragment = ""
            fragments.append(clause)
            continue

        current_semantic_len = get_semantic_length(current_fragment)
        if current_semantic_len + clause_semantic_len <= max_len:
            current_fragment += clause
        else:
            if current_fragment:
                fragments.append(current_fragment)
            current_fragment = clause

    if current_fragment:
        fragments.append(current_fragment)

    return fragments


def calibrate_positions(fragments, positions, original_text):
    """
    校准fragments和positions的对齐关系
    """
    calibrated_positions = {}
    current_global_pos = 0
    
    for frag_idx, fragment in enumerate(fragments):
        # 在原始文本中查找当前片段的位置
        frag_len = len(fragment)
        found_pos = original_text.find(fragment, current_global_pos)
        
        if found_pos == -1:
            # 如果找不到，尝试放宽条件（如忽略空格差异）
            simplified_frag = fragment.replace(" ", "")
            simplified_original = original_text.replace(" ", "")
            found_pos = simplified_original.find(simplified_frag, current_global_pos)
            if found_pos != -1:
                # 找到后映射回原始位置
                non_space_count = original_text[:found_pos].count(" ")
                found_pos += non_space_count
        
        if found_pos == -1:
            # 如果仍然找不到，使用原positions中的值（降级处理）
            if frag_idx in positions:
                calibrated_positions[frag_idx] = positions[frag_idx]
            else:
                calibrated_positions[frag_idx] = (current_global_pos, current_global_pos + frag_len)
            continue
            
        calibrated_positions[frag_idx] = (found_pos, found_pos + frag_len)
        current_global_pos = found_pos + frag_len
    
    return calibrated_positions


def cut_text_by_semantic_length(text, max_semantic_length=24, min_tail_length=5):
    """
    按照语义长度划分文本，保持语义单元的完整性，并返回位置信息
    Args:
        text: 输入文本
        max_semantic_length: 目标语义长度，无标点的完整子句允许超过该值
        min_tail_length: 尾部最小长度
    Returns:
        dict: {
            "fragments": List[str],  # 分割后的文本片段列表
            "positions": Dict[int, Tuple[int, int]]  # 子句位置信息（key为顺序，value为(起始index, 结束index)）
        }
    """
    if not has_valid_content(text):
        return {"fragments": [], "positions": {}}

    # 保存原始文本用于位置计算
    original_text = text
    # 定义一个独特的占位符
    DOT_PLACEHOLDER = "##DOT##"
    
    # 保护小数点和特定缩写中的点
    # 使用正则表达式查找数字中的点（如 3.14）和常见缩写中的点（如 U.S.A.）
    # 并将它们替换为占位符
    # `\d\.\d` 匹配数字间的小数点
    # `([A-Z])\.([A-Z])` 匹配大写字母间的点

    # 用前后断言，连续的点（如 2.5.1）也能全部保护
    processed_text = re.sub(r'(?<=\d)\.(?=\d)', DOT_PLACEHOLDER, text)
    for _ in range(3):
        processed_text = re.sub(r'([A-Z])\.([A-Z])', r'\1' + DOT_PLACEHOLDER + r'\2', processed_text)
    # 保护千位分隔符（如 1,234,567），否则下面会被当作子句边界的“，”
    # 占位符用一个私用区字符，不计入语义长度
    COMMA_PLACEHOLDER = "\ue000"
    processed_text = re.sub(r'(?<=\d),(?=\d{3}(?!\d))', COMMA_PLACEHOLDER, processed_text)

    processed_text = processed_text.replace("\n", " ").replace("。，", "。")
    
    if get_semantic_length(processed_text) <= max_semantic_length:
        # 返回前恢复占位符
        return {
            "fragments": [processed_text.replace(DOT_PLACEHOLDER, ".").replace(COMMA_PLACEHOLDER, ",")],
            "positions": {0: (0, len(text))}  # 整个文本的位置
        }

    # 标点标准化（只在处理时使用，不影响原始位置计算）
    normalized_text = processed_text.replace(".", "。").replace("!", "！").replace("?", "？").replace(",", "，")
    
    result_fragments = []
    position_map = {}
    global_offset = 0  # 跟踪在原始文本中的位置

    # 第一阶段：按句子分割
    sentences = []
    sentence_positions = []
    current_sentence = ""
    start_idx = 0
    
    for i, char in enumerate(normalized_text):
        current_sentence += char
        if char in "。！？": # 移除了 '.' 和 '!' '?'
            sentence = current_sentence.strip()
            if sentence:
                sentences.append(sentence)
                sentence_positions.append((start_idx, i + 1))  # 包含标点的结束位置
            current_sentence = ""
            start_idx = i + 1

    # 处理最后一个句子
    if current_sentence:
        # 如果最后一部分没有标点，可以补上，也可以不补，保持原逻辑
        sentences.append(current_sentence.strip())
        sentence_positions.append((start_idx, len(normalized_text)))
        if not sentences[-1].endswith(("。", "！", "？")):
             sentences[-1] += "。"

    # 第二阶段：处理每个句子
    fragment_counter = 0
    for sent_idx, (sentence, (sent_start, sent_end)) in enumerate(zip(sentences, sentence_positions)):
        clauses = []
        clause_positions = []
        current_clause = ""
        clause_start = 0
        
        for i, char in enumerate(sentence):
            current_clause += char
            if char in "，;；": # 移除了 ','
                clause = current_clause.strip()
                if clause and has_valid_content(clause):
                    clauses.append(clause)
                    clause_positions.append((clause_start, i + 1))  # 在句子中的相对位置
                elif clause and clauses:
                    clauses[-1] += clause
                    clause_positions[-1] = (clause_positions[-1][0], i + 1)
                current_clause = ""
                clause_start = i + 1

        if current_clause:
            clause = current_clause.strip()
            if clause and has_valid_content(clause):
                clauses.append(clause)
                clause_positions.append((clause_start, len(sentence)))
            elif clause and clauses:
                clauses[-1] += clause
                clause_positions[-1] = (clause_positions[-1][0], len(sentence))

        # 第三阶段：处理每个子句
        i = 0
        while i < len(clauses):
            clause = clauses[i]
            clause_start_in_sent, clause_end_in_sent = clause_positions[i]
            
            # 计算在原始文本中的绝对位置
            abs_start = sent_start + clause_start_in_sent
            abs_end = sent_start + clause_end_in_sent
            
            clause_semantic_len = get_semantic_length(clause)

            # 如果当前子句很短，则尝试与下一个子句聚合
            if clause_semantic_len < min_tail_length and i + 1 < len(clauses):
                next_clause = clauses[i + 1]
                next_start, next_end = clause_positions[i + 1]
                combined_clause = clause + next_clause
                combined_semantic_len = get_semantic_length(combined_clause)
                # 如果聚合后的子句不超过最大长度，则聚合
                if combined_semantic_len <= max_semantic_length:
                    result_fragments = append_text_fragment(result_fragments, combined_clause, max_semantic_length, min_tail_length)
                    # 合并位置信息
                    merged_position = (abs_start, sent_start + next_end)
                    position_map[fragment_counter] = merged_position
                    fragment_counter += 1
                    i += 2
                    continue

            # 如果子句仍然超过最大长度，则进一步分割
            if clause_semantic_len > max_semantic_length:
                sub_fragments = split_long_fragment(clause, max_semantic_length)
                # 等分位置（简化处理，实际应根据语义分割调整）
                frag_len = len(clause)
                sub_frag_count = len(sub_fragments)
                for j, frag in enumerate(sub_fragments):
                    result_fragments = append_text_fragment(result_fragments, frag, max_semantic_length, min_tail_length)
                    frag_len_part = len(frag)
                    frag_start = abs_start + j * (frag_len // sub_frag_count)
                    frag_end = frag_start + frag_len_part
                    position_map[fragment_counter] = (frag_start, frag_end)
                    fragment_counter += 1
            else:
                result_fragments = append_text_fragment(result_fragments, clause, max_semantic_length, min_tail_length)
                position_map[fragment_counter] = (abs_start, abs_end)
                fragment_counter += 1
            i += 1


    # 最终返回结果前，恢复所有片段中的占位符
    final_result = [frag.replace(DOT_PLACEHOLDER, ".").replace(COMMA_PLACEHOLDER, ",") for frag in result_fragments]

    calibrated_positions = calibrate_positions(final_result, position_map, original_text)
    return {
        "fragments": final_result,
        "positions": calibrated_positions
    }

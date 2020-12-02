import sys
import pickle as pkl
import array
import os
import timeit
import contextlib


# 将字符串和数字ID进行相互映射
class IdMap:
    """Helper class to store a mapping from strings to ids."""

    def __init__(self):
        self.str_to_id = {}
        self.id_to_str = []

    def __len__(self):
        """Return number of terms stored in the IdMap"""
        return len(self.id_to_str)

    def _get_str(self, i):
        """Returns the string corresponding to a given id (`i`)."""
        ### Begin your code
        return self.id_to_str[i]
        ### End your code

    def _get_id(self, s):
        """Returns the id corresponding to a string (`s`).
        If `s` is not in the IdMap yet, then assigns a new id and returns the new id.
        """
        ### Begin your code
        # 如果idmap里面没有，字典和list都要添加
        if s not in self.str_to_id.keys():
            self.str_to_id[s] = len(self.str_to_id)
            self.id_to_str.append(s)
        return self.str_to_id[s]
        ### End your code

    def __getitem__(self, key):
        """If `key` is a integer, use _get_str;
           If `key` is a string, use _get_id;"""
        if type(key) is int:
            return self._get_str(key)
        elif type(key) is str:
            return self._get_id(key)
        else:
            raise TypeError


# 将倒排列表编码成字节流列表。输入一个int数组，编码后变成一个字符串，解码后返回该int数组
class UncompressedPostings:

    @staticmethod
    def encode(postings_list):  # 编码
        return array.array('L', postings_list).tobytes()

    @staticmethod
    def decode(encoded_postings_list):  # 解码
        decoded_postings_list = array.array('L')
        decoded_postings_list.frombytes(encoded_postings_list)
        return decoded_postings_list.tolist()


# 磁盘上的倒排索引，源文件
class InvertedIndex:
    """A class that implements efficient reads and writes of an inverted index
    to disk

    Attributes
    ----------
    postings_dict: Dictionary mapping: termID->(start_position_in_index_file,
                                                number_of_postings_in_list,
                                               length_in_bytes_of_postings_list)
        This is a dictionary that maps from termIDs to a 3-tuple of metadata
        that is helpful in reading and writing the postings in the index file
        to/from disk. This mapping is supposed to be kept in memory.
        start_position_in_index_file is the position (in bytes) of the postings
        list in the index file
        number_of_postings_in_list is the number of postings (docIDs) in the
        postings list
        length_in_bytes_of_postings_list is the length of the byte
        encoding of the postings list

    terms: List[int]
        A list of termIDs to remember the order in which terms and their
        postings lists were added to index.

        After Python 3.7 we technically no longer need it because a Python dict
        is an OrderedDict, but since it is a relatively new feature, we still
        maintain backward compatibility with a list to keep track of order of
        insertion.
    """

    # 索引名，编码方式（最后自己可以修改编码方式）
    def __init__(self, index_name, postings_encoding=None, directory=''):
        """
        Parameters
        ----------
        index_name (str): Name used to store files related to the index
        postings_encoding: A class implementing static methods for encoding and
            decoding lists of integers. Default is None, which gets replaced
            with UncompressedPostings
        directory (str): Directory where the index files will be stored
        """

        self.index_file_path = os.path.join(directory, index_name + '.index')
        self.metadata_file_path = os.path.join(directory, index_name + '.dict')

        if postings_encoding is None:
            self.postings_encoding = UncompressedPostings
        else:
            self.postings_encoding = postings_encoding
        self.directory = directory

        self.postings_dict = {}
        self.terms = []  # Need to keep track of the order in which the
        # terms were inserted. Would be unnecessary
        # from Python 3.7 onwards

    def __enter__(self):
        """Opens the index_file and loads metadata upon entering the context"""
        # Open the index file
        self.index_file = open(self.index_file_path, 'rb+')

        # Load the postings dict and terms from the metadata file
        with open(self.metadata_file_path, 'rb') as f:
            self.postings_dict, self.terms = pkl.load(f)
            self.term_iter = self.terms.__iter__()

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Closes the index_file and saves metadata upon exiting the context"""
        # Close the index file
        self.index_file.close()

        # Write the postings dict and terms to the metadata file
        with open(self.metadata_file_path, 'wb') as f:
            pkl.dump([self.postings_dict, self.terms], f)


# BSBI：基于磁盘的外部排序构建索引
# 将每一个子目录当做一个块（block），并且在构建索引的过程中每次只能加载一个块
class BSBIIndex:
    """
    Attributes
    ----------
    term_id_map(IdMap): For mapping terms to termIDs
    doc_id_map(IdMap): For mapping relative paths of documents (eg
        0/3dradiology.stanford.edu_) to docIDs
    data_dir(str): Path to data
    output_dir(str): Path to output index files
    index_name(str): Name assigned to index
    postings_encoding: Encoding used for storing the postings.
        The default (None) implies UncompressedPostings
    """

    def __init__(self, data_dir, output_dir, index_name="BSBI",
                 postings_encoding=None):
        self.term_id_map = IdMap()
        self.doc_id_map = IdMap()
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.index_name = index_name
        self.postings_encoding = postings_encoding

        # Stores names of intermediate indices
        self.intermediate_indices = []

    # 把文档->文档id和词语->词语id的映射表保存到字典output_dir中
    def save(self):
        """Dumps doc_id_map and term_id_map into output directory"""

        with open(os.path.join(self.output_dir, 'terms.dict'), 'wb') as f:
            pkl.dump(self.term_id_map, f)
        with open(os.path.join(self.output_dir, 'docs.dict'), 'wb') as f:
            pkl.dump(self.doc_id_map, f)

    # 从字典output_dir中读取映射表
    def load(self):
        """Loads doc_id_map and term_id_map from output directory"""

        with open(os.path.join(self.output_dir, 'terms.dict'), 'rb') as f:
            self.term_id_map = pkl.load(f)
        with open(os.path.join(self.output_dir, 'docs.dict'), 'rb') as f:
            self.doc_id_map = pkl.load(f)

    # 构建索引
    def index(self):
        """Base indexing code

        This function loops through the data directories,
        calls parse_block to parse the documents
        calls invert_write, which inverts each block and writes to a new index
        then saves the id maps and calls merge on the intermediate indices
        """
        print("start index...")
        # block_dir_relative是一个子目录，下面有若干文档，这个子目录就是读取的单位（块）
        for block_dir_relative in sorted(next(os.walk(self.data_dir))[1]):
            td_pairs = self.parse_block(block_dir_relative)  # 解析出来所有映射对

            index_id = 'index_' + block_dir_relative
            self.intermediate_indices.append(index_id)
            with InvertedIndexWriter(index_id, directory=self.output_dir,
                                     postings_encoding=
                                     self.postings_encoding) as index:
                self.invert_write(td_pairs, index)  # 将这一块的所有映射对合并成倒排列表，并写入index文件
                td_pairs = None
        self.save()

        with InvertedIndexWriter(self.index_name, directory=self.output_dir,
                                 postings_encoding=
                                 self.postings_encoding) as merged_index:
            with contextlib.ExitStack() as stack:
                indices = [stack.enter_context(
                    InvertedIndexIterator(index_id,
                                          directory=self.output_dir,
                                          postings_encoding=self.postings_encoding))
                    for index_id in self.intermediate_indices]
                self.merge(indices, merged_index)  # 将所有index文档合并成大的索引文件

    # 读取子目录block_dir_relative下的所有文档，解析出来映射对的列表，形如[(word1,file1),(word2,file1)]
    # 注意第二个参数是file号不是block号
    def parse_block(self, block_dir_relative):
        """Parses a tokenized text file into termID-docID pairs

        Parameters
        ----------
        block_dir_relative : str
            Relative Path to the directory that contains the files for the block

        Returns
        -------
        List[Tuple[Int, Int]]
            Returns all the td_pairs extracted from the block

        Should use self.term_id_map and self.doc_id_map to get termIDs and docIDs.
        These persist across calls to parse_block
        """
        ### Begin your code
        print("start parse_block ",block_dir_relative,"...")
        td_pairs = []
        path = os.path.join(self.data_dir, block_dir_relative)
        for doc_name in os.listdir(path):
            with open(os.path.join(path, doc_name), 'r')as f:
                for line in f.readlines():
                    words = line.split(' ')  # 该文档中的所有单词
                    for word in words:
                        td_pairs.append((self.term_id_map[word.strip()],
                                         self.doc_id_map[os.path.join(block_dir_relative, doc_name)]))
        return td_pairs

        ### End your code

    # 将解析得到的td_pairs转换成倒排表，并使用InvertedIndexWriter类将其写入磁盘index文件。
    def invert_write(self, td_pairs, index):
        """Inverts td_pairs into postings_lists and writes them to the given index

        Parameters
        ----------
        td_pairs: List[Tuple[Int, Int]]
            List of termID-docID pairs
        index: InvertedIndexWriter
            Inverted index on disk corresponding to the block
        """
        ### Begin your code
        print("start invert_write...")

        td_pairs = sorted(td_pairs, key=lambda x: self.term_id_map[x[0]])# 必须先按字典序排序

        dic = {}
        for pair in td_pairs:
            if pair[0] not in dic.keys():
                dic[pair[0]] = [pair[1]]
            else:
                dic[pair[0]].append(pair[1])
        term_list = []
        post_list = []
        for term in dic.keys():
            term_list.append(term)
        for post in dic.values():
            post_list.append(post)

        # 自动编码，写入磁盘
        for i in range(len(dic)):
            index.append(term_list[i], list(set(post_list[i])))
            # 直接append就是写入磁盘了（注意需要用set去重[1,1]->[1]）
        ### End your code


    # 查询语句为空格隔开的单词
    def retrieve(self, query):
        """Retrieves the documents corresponding to the conjunctive query

        Parameters
        ----------
        query: str
            Space separated list of query tokens

        Result
        ------
        List[str]
            Sorted list of documents which contains each of the query tokens.
            Should be empty if no documents are found.

        Should NOT throw errors for terms not in corpus
        """
        if len(self.term_id_map) == 0 or len(self.doc_id_map) == 0:
            self.load()

        ### Begin your code
        words = [token.strip() for token in query.split(' ')] # 先去两边换行符再去空格
        terms = []
        for word in words:
            terms.append(self.term_id_map[word])
        with InvertedIndexMapper(self.index_name,
                                 directory=self.output_dir,
                                 postings_encoding=self.postings_encoding) as mapper:
            result = mapper[terms[0]]
            for term in terms[1:]:
                result = sorted_intersect(result, mapper[term])
        result=[self.doc_id_map[i] for i in result]
        return sorted(result)
        ### End your code



# 将倒排记录表写入索引文件
class InvertedIndexWriter(InvertedIndex):
    """"""

    def __enter__(self):
        self.index_file = open(self.index_file_path, 'wb+')
        return self

    # 将倒排记录表写到文件最后
    def append(self, term, postings_list):
        """Appends the term and postings_list to end of the index file.

        This function does three things,
        1. Encodes the postings_list using self.postings_encoding
        2. Stores metadata in the form of self.terms and self.postings_dict
           Note that self.postings_dict maps termID to a 3 tuple of
           (start_position_in_index_file,
           number_of_postings_in_list,
           length_in_bytes_of_postings_list)
        3. Appends the bytestream to the index file on disk

        Hint: You might find it helpful to read the Python I/O docs
        (https://docs.python.org/3/tutorial/inputoutput.html) for
        information about appending to the end of a file.

        Parameters
        ----------
        term:
            term or termID is the unique identifier for the term
        postings_list: List[Int]
            List of docIDs where the term appears
        """
        ### Begin your code
        # 进行编码
        self.terms.append(term)
        # seek(0,2)结尾指针
        postings_list=sorted(postings_list)# 这个sort特别重要，因为VB编码必须前<后，才能转二进制
        encoded=self.postings_encoding.encode(postings_list)
        self.postings_dict[term] = (self.index_file.seek(0, 2), len(postings_list), len(encoded))
        self.index_file.write(encoded)
        ### End your code



# 迭代地从磁盘（self.index_file）上每次读取文件的一个倒排列表
class InvertedIndexIterator(InvertedIndex):
    """"""

    def __enter__(self):
        """Adds an initialization_hook to the __enter__ function of super class
        """
        super().__enter__()
        self._initialization_hook()
        return self

    # 第一条倒排列表
    def _initialization_hook(self):
        """Use this function to initialize the iterator
        """
        ### Begin your code
        self.cnt = 0
        ### End your code

    def __iter__(self):
        return self

    def __next__(self):
        """Returns the next (term, postings_list) pair in the index.

        Note: This function should only read a small amount of data from the
        index file. In particular, you should not try to maintain the full
        index file in memory.
        """
        ### Begin your code
        if self.cnt == len(self.terms):
            raise StopIteration
        term = self.terms[self.cnt]
        start_position_in_index_file, number_of_postings_in_list, length_in_bytes_of_postings_list = \
            self.postings_dict[term]  # 存储倒排列表时的3个参数，接下来要根据这三个参数来找每一个倒排列表
        """
        file.seek(offset,whence) whence=0：开头；1：当前位置；2：结尾。offset：在whence的基础上开始读
        file.read(offset)：从seek指针的位置开始读offset字节
        """
        self.index_file.seek(start_position_in_index_file, 0)
        encoded = self.index_file.read(length_in_bytes_of_postings_list)
        decoded = self.postings_encoding.decode(encoded)
        self.cnt += 1
        return term, decoded
        ### End your code

    def delete_from_disk(self):
        """Marks the index for deletion upon exit. Useful for temporary indices
        """
        self.delete_upon_exit = True

    def __exit__(self, exception_type, exception_value, traceback):
        """Delete the index file upon exiting the context along with the
        functions of the super class __exit__ function"""
        self.index_file.close()
        if hasattr(self, 'delete_upon_exit') and self.delete_upon_exit:
            os.remove(self.index_file_path)
            os.remove(self.metadata_file_path)
        else:
            with open(self.metadata_file_path, 'wb') as f:
                pkl.dump([self.postings_dict, self.terms], f)



import heapq

class BSBIIndex(BSBIIndex):
    # 合并打开的倒排列表InvertedIndexIterator，文档列表已经排过序了，那么我们可以在线性时间内对它们进行合并排序
    # indices是一个包含若干(1, [2, 3, 4])的列表（iter类型，必须用for来遍历）
    # merged_index是要写入的磁盘文档
    # merged_index是InvertedIndexWriter类型，直接用append(1, [2, 3, 4])
    def merge(self, indices, merged_index):
        """Merges multiple inverted indices into a single index

        Parameters
        ----------
        indices: List[InvertedIndexIterator]
            A list of InvertedIndexIterator objects, each representing an
            iterable inverted index for a block
        merged_index: InvertedIndexWriter
            An instance of InvertedIndexWriter object into which each merged
            postings list is written out one at a time
        """
        ### Begin your code
        # 先把每个文档的indices中的tuple放进一个大list
        last_term = ''
        last_postings = []
        # 按字典序排序读取term_id，和invert_write中对应
        for term_id, postings in heapq.merge(*indices, key=lambda x: self.term_id_map[x[0]]):
            if term_id!=last_term:
                if term_id!='':
                    merged_index.append(last_term,last_postings)#将上次的tuple导入文件
                last_term=term_id
                last_postings=postings# 更新last
            else:# 否则进行合并
                last_postings=self.or_list(postings,last_postings)
        if last_term:
            merged_index.append(last_term, last_postings)


    ### End your code

    def or_list(self, files1, files2):
        files1 = sorted(files1)
        files2 = sorted(files2)
        result = []
        i = j = 0
        while i < len(files1) and j < len(files2):
            if files1[i] == files2[j]:
                result.append(files1[i])
                i += 1
                j += 1
            elif files1[i] < files2[j]:
                result.append(files1[i])
                i += 1
            else:
                result.append(files2[j])
                j += 1

        if i < len(files1):
            result += files1[i:]
        if j < len(files2):
            result += files2[j:]
        return result
# 布尔联合检索
# 在postings_dict中找到term在总索引文件中位置并取出它的倒排记录表
class InvertedIndexMapper(InvertedIndex):
    def __getitem__(self, key):
        return self._get_postings_list(key)

    def _get_postings_list(self, term):
        """Gets a postings list (of docIds) for `term`.

        This function should not iterate through the index file.
        I.e., it should only have to read the bytes from the index file
        corresponding to the postings list for the requested term.
        """
        ### Begin your code
        start_position_in_index_file, number_of_postings_in_list, length_in_bytes_of_postings_list = \
            self.postings_dict[term]
        self.index_file.seek(start_position_in_index_file, 0)
        decoded = self.postings_encoding.decode(self.index_file.read(length_in_bytes_of_postings_list))
        return decoded
        ### End your code


# 列表求交集
def sorted_intersect(files1, files2):
    """Intersects two (ascending) sorted lists and returns the sorted result

    Parameters
    ----------
    list1: List[Comparable]
    list2: List[Comparable]
        Sorted lists to be intersected

    Returns
    -------
    List[Comparable]
        Sorted intersection
    """
    ### Begin your code
    i = j = 0
    result = []
    while i < len(files1) and j < len(files2):
        if files1[i] == files2[j]:
            result.append(files1[i])
            i += 1
            j += 1
        elif files1[i] < files2[j]:
            i+=1
        else:
            j+=1
    return result
    ### End your code

# 索引压缩，可变长编码
# VariableByte
class VariableByteCompressedPostings:
    @staticmethod
    def get_decoded(n):
        bina = bin(n)[2:]
        result = []
        cnt = 0
        piece = ''
        for i in range(len(bina) - 1, -1, -1):
            if cnt == 6 or i == 0:
                cnt = 0
                piece = bina[i] + piece
                result.append(piece.zfill(8))
                piece = ''
            else:
                cnt += 1
                piece = bina[i] + piece
        for i in range(1, len(result)):
            result[i] = '1' + result[i][1:]
        result.reverse()
        return result

    @staticmethod
    def encode(postings_list):
        """Encodes `postings_list` using gap encoding with variable byte
        encoding for each gap

        Parameters
        ----------
        postings_list: List[int]
            The postings list to be encoded

        Returns
        -------
        bytes:
            Bytes reprsentation of the compressed postings list
            (as produced by `array.tobytes` function)
        """
        ### Begin your code
        GAP_STEP = 20  # 步长
        n = len(postings_list)
        encoded = []
        edge = 0
        for i in range(0, n):
            if i % GAP_STEP == 0:
                edge = postings_list[i]
                enc = VariableByteCompressedPostings.get_decoded(postings_list[i])
                for item in enc:
                    encoded.append(int(item, 2))
            else:
                enc = VariableByteCompressedPostings.get_decoded(postings_list[i] - edge)
                for item in enc:
                    encoded.append(int(item, 2))
        encoded = bytes(encoded)
        return encoded

    @staticmethod
    def decode(encoded_postings_list):
        """Decodes a byte representation of compressed postings list

        Parameters
        ----------
        encoded_postings_list: bytes
            Bytes representation as produced by `CompressedPostings.encode`

        Returns
        -------
        List[int]
            Decoded postings list (each posting is a docIds)
        """
        ### Begin your code
        GAP_STEP = 20  # 步长

        decoded = []
        temp = 0  # 非终结的临时值
        gap = 0  # 每个step的首元素
        append_cnt = 0  # 记录append的次数，次数+1为步长时说明下一个元素是gap
        for i in range(len(encoded_postings_list)):
            bina = bin(encoded_postings_list[i])[2:]
            if len(bina) == 8:
                temp = temp * 128 + int(bina, 2) % 128  # 8位说明没结束
            else:
                if append_cnt % GAP_STEP == 0:  # 对于每个step的首元素gap，终结为本身的值
                    gap = temp * 128 + int(bina, 2)
                    decoded.append(gap)
                else:  # 非首元素，终结要加上gap
                    temp = temp * 128 + int(bina, 2) + gap
                    decoded.append(temp)
                    if (append_cnt + 1) % GAP_STEP == 0:  # 如果当前step内已经处理完了，gap要重新初始化
                        gap = 0
                append_cnt += 1
                temp = 0
        return decoded
        ### End your code

# gamma编码
class GammaCompressedPostings:
    @staticmethod
    def get_gamma(n):
        result=[]
        bina=bin(n)[2:]
        gamma='0'+bina[1:]
        for i in range(len(bina)-1):
            gamma='1'+gamma
        piece=gamma[0]
        for i in range(1,len(gamma)):
            if i%8==0:
                result.append(piece)
                piece=gamma[i]
            else:
                piece += gamma[i]
        if piece:
            result.append(piece)
        return result

    @staticmethod
    def encode(postings_list):
        postings_list=[i+1 for i in postings_list]
        GAP_STEP = 20  # 步长
        n = len(postings_list)
        encoded = ""
        edge = 0
        for i in range(0, n):
            if i % GAP_STEP == 0:
                edge = postings_list[i]
                enc = GammaCompressedPostings.get_gamma(postings_list[i])
                for item in enc:
                    encoded+=item
            else:
                enc = GammaCompressedPostings.get_gamma(postings_list[i] - edge)
                for item in enc:
                    encoded+=item
        encoded=encoded.ljust((7+len(encoded))//8*8,'1')# 末尾补1，decode时方便表示结束
        encoded_list=[]
        for i in range(len(encoded)//8):
            bina=encoded[8*i:8*i+8]
            encoded_list.append(int(bina,2))
        encoded_list = bytes(encoded_list)
        return encoded_list

    @staticmethod
    def decode(encoded_postings_list):
        GAP_STEP = 20  # 步长
        bina_list = ""
        for i in range(len(encoded_postings_list)):
            bina_list += bin(encoded_postings_list[i])[2:].zfill(8)  # 一定要记得补0，转为二进制会忽略前导0！
        result = []
        i = 0
        cnt = 0

        append_cnt = 0
        gap = 0
        while i < len(bina_list):
            while bina_list[i] == '1':
                cnt += 1
                i += 1
                if i == len(bina_list):
                    break
            if i == len(bina_list):
                break
            piece = '1'
            i += 1  # skip zero after some 1s
            piece += bina_list[i:i + cnt]
            if append_cnt % GAP_STEP == 0:
                gap = int(piece, 2)
                result.append(gap)
            else:
                result.append(int(piece, 2) + gap)
            append_cnt += 1
            i = i + cnt
            cnt = 0
        result = [i - 1 for i in result]
        return result


# 测试代码

def short_test():
    toy_dir='toy-data'
    BSBI_instance = BSBIIndex(data_dir=toy_dir, output_dir = 'vb_toy_output_dir',
                              postings_encoding=None)
                              #VariableByteCompressedPostings)
    #BSBI_instance.index()
    BSBI_instance.load()
    print(BSBI_instance.retrieve("you"))

def long_test():
    BSBI_instance = BSBIIndex(data_dir='pa1-data', output_dir='output_dir',)
    BSBI_instance.index()
    BSBI_instance.load()
    for i in range(1, 9):
        print(i)
        with open('dev_queries/query.' + str(i)) as q:
            query = q.read()
            my_results = [os.path.normpath(path) for path in BSBI_instance.retrieve(query)]
            with open('dev_output/' + str(i) + '.out') as o:
                reference_results = [os.path.normpath(x.strip()) for x in o.readlines()]
                print(len(my_results),len(reference_results))
                assert my_results == reference_results, "Results DO NOT match for query: " + query.strip()
            print("Results match for query:", query.strip())

def long_test_vb():
    BSBI_instance = BSBIIndex(data_dir='pa1-data', output_dir='vb_output_dir',
                              postings_encoding=VariableByteCompressedPostings)
    # BSBI_instance.index()
    BSBI_instance.load()
    print(len(BSBI_instance.term_id_map.id_to_str))
    for i in range(1, 9):
        print(i)
        with open('dev_queries/query.' + str(i)) as q:
            query = q.read()
            my_results = [os.path.normpath(path) for path in BSBI_instance.retrieve(query)]
            with open('dev_output/' + str(i) + '.out') as o:
                reference_results = [os.path.normpath(x.strip()) for x in o.readlines()]
                print(len(my_results),len(reference_results))
                assert my_results == reference_results, "Results DO NOT match for query: " + query.strip()
            print("Results match for query:", query.strip())

def long_test_gamma():
    BSBI_instance = BSBIIndex(data_dir='pa1-data', output_dir='gm_output_dir',
                              postings_encoding=GammaCompressedPostings)
    #BSBI_instance.index()
    BSBI_instance.load()
    print(len(BSBI_instance.retrieve("stanford class")))
    print(len(BSBI_instance.term_id_map.id_to_str))
    for i in range(1, 9):
        print(i)
        with open('dev_queries/query.' + str(i)) as q:
            query = q.read()
            my_results = [os.path.normpath(path) for path in BSBI_instance.retrieve(query)]
            with open('dev_output/' + str(i) + '.out') as o:
                reference_results = [os.path.normpath(x.strip()) for x in o.readlines()]
                print(len(my_results), len(reference_results))
                assert my_results == reference_results, "Results DO NOT match for query: " + query.strip()
            print("Results match for query:", query.strip())

long_test()
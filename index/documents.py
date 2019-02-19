from bs4 import BeautifulSoup
from bs4.element import Comment
import re


class Document(object):

    def __init__(self, doc_id, file = None, line = None):
        if file is not None and line is None:
            name = file.name
            if str(file.name).startswith('Users/tweni/Documents/workspace/SIRS/data/'):
                name = file.name[len('Users/tweni/Documents/workspace/SIRS/data/'):]
            self.name = name
            self.doc_id = doc_id
            self.num_tokens = dict()
            self.resources = dict()
        elif file is None and line is not None:
            self.name = ''
            self.doc_id = doc_id
            self.num_tokens = dict()
            self.resources = dict()
            self.read_from_index(line)
        else:
            raise Exception('Must pass either file or line')

    def get_name(self):
        return self.name

    def get_doc_id(self):
        return self.doc_id

    def get_num_tokens(self, field):
        return self.num_tokens[field]

    def get_resources(self):
        return self.resources

    def write_to_index(self):
        """
        Creates a String to write to direct document index including all extra information. This is expected to be
        overridden by subclasses
        :return: String representation of a document
        """

        sb = list()
        sb.append(str(self.get_doc_id()) + '\t' + self.get_name() + '\t' + self.print_num_tokens())
        for k,v in self.resources.items():
            sb.append(k + '-#-' + v)

        sb.append('\n')
        return '\t'.join(sb)

    def print_num_tokens(self):
        sb = list()
        for k,v in self.num_tokens.items():
            sb.append(str(k) + ':' + str(v))
        return ','.join(sb)

    def read_from_index(self, line):
        """
        Reads data that was previous written to file by writeToIndex() function.
        Should be overridden when writeToIndex is overridden

        :param line: line to read
        :return:
        """
        s = line.split('\t')
        self.doc_id = s[0]
        self.name = s[1]
        num_toks_list = s[2].split(',')
        for toks in num_toks_list:
            r = toks.split(':')
            f = Field(int(r[0]))
            self.num_tokens[f.field] = int(r[1])

        for i in range(3,len(s)):
            r = s[i].split('-#-')
            if len(r) == 2:
                str(r[1]).replace('"', '')
                self.resources[r[0]] = r[1]


class HTMLDocument(Document):
    def __init__(self, doc_id, file, line):
        if file is not None and line is None:
            super().__init__(doc_id, file=file)
        elif file is None and line is not None:
            super().__init__(doc_id, line=line)
        else:
            raise Exception('Must pass either file or line')

    @staticmethod
    def tag_visible(element):
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True

    @staticmethod
    def text_from_html(body):
        texts = body.findAll(text=True)
        visible_texts = filter(HTMLDocument.tag_visible, texts)
        return u" ".join(t.strip() for t in visible_texts)

    def parse(self, doc_id, file):
        print('HTML Parsing invoked')
        f = Fields()
        f.add_field('body')
        f.add_field('link')
        f.add_field('title')

        html = b''.join(file.readlines())
        tokens = list()
        tokenizer = WhitespaceTokenizer()
        normalizer = CaseFoldingNormalizer()

        doc = BeautifulSoup(html, features='lxml')

        # remove all script and style elements
        for script in doc(["script", "style"]):
            script.extract()

        titles = [title.get_text() for title in doc.find_all('title')]
        num_title_tokens = 0
        if len(titles) >= 1:
            title = titles[0]
            self.resources['title'] = title.replace('\n', ' ')
            title_tokens = tokenizer.tokenizer_str(title)
            title_tokens = normalizer.normalize(title_tokens)
            for tok in title_tokens:
                tokens.append(Token(tok, Fields().get_field_id('title')))
                num_title_tokens += 1
        self.num_tokens[Fields().get_field_id('title')] = num_title_tokens
        text = HTMLDocument.text_from_html(doc)

        content = tokenizer.tokenizer_str(text)
        content = normalizer.normalize(content)
        content_toks = 0
        for s in content:
            tokens.append(Token(s, Fields().get_field_id('body')))
            content_toks += 1
        self.num_tokens[Fields().get_field_id('body')] = content_toks


        for link in doc.find_all('a', href=True):
            url = link['href']
            #parse.urljoin(web_url, link['href'])
            anchor_toks = list()
            anchors = tokenizer.tokenizer_str(link.text)
            anchors = normalizer.normalize(anchors)
            for s in anchors:
                anchor_toks.append(Token(s, Fields().get_field_id('link')))
            self.resources['l'+url] = anchor_toks
        #self.num_tokens[Fields.get_field_id('link')] = len(anchor_toks)
        return tokens


class Fields(object):

    class __Fields:

        def __init__(self):
            self.__fields = dict()
            self.__weights = dict()

    instance = None

    def __init__(self):
        if not Fields.instance:
            Fields.instance = Fields.__Fields()
        else:
            pass

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def add_field(self, field):
        if field in Fields.instance.__fields:
            return False
        else:
            new_field = Field(len(self.__fields))
            self.__fields[field] = new_field

    def get_field_id(self, field):
        return self.__fields[field].field

    def get_fields(self):
        return self.__fields.values()

    def get_items(self):
        return self.__fields.items()

    def get_weight(self, field):
        return self.__weights[field]

    @staticmethod
    def load_from_inverted_index(field_string):
        me = Fields()
        fs = field_string.strip().split(';')
        for f in fs:
            fl = f.split(',')
            me.__fields[fl[0]] = Field(int(fl[1]))

        w = float(1)/len(me.__fields)

        for k in me.__fields.values():
            me.__weights[k.field] = w

    def assign_weights(self, weights):
        for k,v in weights.items():
            self.__weights[self.get_field_id(k)] = v

        # normalize
        __sum = 0.0
        for w in self.__weights.values():
            __sum += w
        for k in self.__weights.keys():
            self.__weights[k] = self.__weights[k]/float(__sum)


class Field(object):
    def __init__(self, field):
        self.field = field

    def __eq__(self, other):
        return self.field == other.args


class Token(object):
    def __init__(self, term, field):
        self.term = term
        self.field = field

    def get_token_string(self):
        return self.term

    def get_field(self):
        return self.field

    def __eq__(self, other):
        return self.field == other.args


class WhitespaceTokenizer(object):
    @staticmethod
    def tokenizer_str(string):
        return re.split('[^a-zA-Z]', string)


class CaseFoldingNormalizer(object):
    @staticmethod
    def normalize(token_list):
        new_list = list()
        for tok in token_list:
            tok = tok.strip()
            if len(tok) == 0 :
                continue
            new_list.append(str(tok).lower())
        return new_list

import csv

import pandas as pd


def data_parser(path, ft='csv', **kwargs):
    if type(path) != str and ft != 'metadatas':
        df = path.copy()
        if type(df) != pd.DataFrame:
            df = pd.DataFrame(df)
    else:
        if path.endswith('.xlsx') or path.endswith('.xls') or ft=='xlsx':
            df = pd.read_excel(path, index_col=False, header=0, **kwargs)
            return df
        if ft == 'csv' and not path.endswith('.xlsx'):
            sniffer = csv.Sniffer()
            sniffer.preferred = [',', '\t', '|']
            dialect = sniffer.sniff(open(path, 'r').readline().strip('\n'))
            param = dict(sep=dialect.delimiter, index_col=False, header=0, low_memory=False,)
            param.update(**kwargs)
            df = pd.read_csv(path, **kwargs)
            return df
            # low_memory is important for sample name look like float and str. it may mistaken the sample name into some float.
        # elif ft == 'metadatas': # indicate there may be multiple input
        #     datas = [data_parser(_,ft='csv',verbose=0) for _ in path]
        #     assert len(set([tuple(_.index) for _ in datas])) == 1  # all datas must have same samples
        #     merged_data = pd.concat(datas, axis=1)
        #     col_dict = {p: list(data.columns) for p, data in zip(path,datas)}
        #     return merged_data, col_dict




def parse_metadata(metadata: pd.DataFrame) -> (dict,pd.DataFrame):
    metadata = data_parser(metadata, ft='csv')
    results = {}
    new_index = []
    for r_idx in metadata.index:
        rat_id = metadata.loc[r_idx, 'ID']
        date = metadata.loc[r_idx, 'date']
        action = metadata.loc[r_idx, 'action']
        raw_stime = metadata.loc[r_idx, 'start']
        raw_etime = metadata.loc[r_idx, 'end']
        adict = {"adaptation": "A",
                 "正式1": "1",
                 "正式2": "2", }
        ## 被写死....注意!!!!!!!!!如果换了新格式的metadata会出错.
        fname = 'R{id}_{action}.avi'.format(id=str(int(rat_id)),
                                            action=adict.get(action, ''))
        results[fname] = (rat_id, date, action, raw_stime, raw_etime)
        new_index.append(fname)
    metadata.index = new_index
    return results, metadata

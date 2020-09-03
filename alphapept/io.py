# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02_io.ipynb (unless otherwise specified).

__all__ = ['HDF_File', 'get_most_abundant', 'load_thermo_raw', 'load_thermo_raw_MSFileReader', 'raw_to_npz',
           'raw_to_npz_parallel', 'load_bruker_raw', 'one_over_k0_to_CCS', 'check_sanity', 'extract_mzml_info',
           'extract_mzxml_info', 'read_mzML', 'read_mzXML', 'list_to_numpy_f32', 'save_query_as_npz', 'MS_Data_File',
           'raw_to_ms_data_file', 'extract_nested', 'extract_mq_settings', 'parse_mq_seq']

# Cell

import h5py
import os
import time
from .__main__ import VERSION_NO


class HDF_File(object):
    '''
    A generic class to store and retrieve on-disk
    data with an HDF container.
    '''

    @property
    def original_file_name(self):
        return self.read(
            attr_name="original_file_name"
        )  # See below for function definition

    @property
    def file_name(self):
        return self.__file_name

    @property
    def directory(self):
        return os.path.dirname(self.file_name)

    @property
    def creation_time(self):
        return self.read(
            attr_name="creation_time"
        )  # See below for function definition

    @property
    def last_updated(self):
        return self.read(
            attr_name="last_updated"
        )  # See below for function definition

    @property
    def version(self):
        return self.read(
            attr_name="version"
        )  # See below for function definition

    @property
    def is_read_only(self):
        return self.__is_read_only

    def __init__(
        self,
        file_name:str,
        is_read_only:bool=True,
        is_new_file:bool=False,
    ):
        self.__file_name = os.path.abspath(file_name)
        if is_new_file:
            is_read_only = False
            if not os.path.exists(self.directory):
                os.makedirs(self.directory)
            with h5py.File(self.file_name, "w") as hdf_file:
                current_time = time.asctime()
                hdf_file.attrs["creation_time"] = current_time
                hdf_file.attrs["original_file_name"] = self.__file_name
                hdf_file.attrs["version"] = VERSION_NO
                hdf_file.attrs["last_updated"] = current_time
        else:
            with h5py.File(self.file_name, "r") as hdf_file:
                self.check()
        self.__is_read_only = is_read_only

    def __eq__(self, other):
        return self.file_name == other.file_name

    def __hash__(self):
        return hash(self.file_name)

    def __str__(self):
        return f"<HDF_File {self.file_name}>"

    def __repr__(self):
        return str(self)

    def check(
        self,
        version:bool=True,
        file_name:bool=True,
    ):
        '''
        Check if the `version` or `file_name` of this HDF_File have changed.
        Return a list of warning messages stating any issues.
        '''
        warning_messages = []
        if version:
            current_version = VERSION_NO
            creation_version = self.version
            if creation_version != current_version:
                warning_messages.append(
                    f"{self} was created with version "
                    f"{creation_version} instead of {current_version}."
                )
        if file_name:
            if self.file_name != self.original_file_name:
                warning_messages.append(
                    f"The file name of {self} has been changed from"
                    f"{self.original_file_name} to {self.file_name}."
                )
        return warning_messages

# Cell

import pandas as pd
from fastcore.foundation import patch


@patch
def read(
    self:HDF_File,
    group_name:str=None,
    dataset_name:str=None,
    attr_name:str=None,
    return_dataset_shape:bool=False,
    return_dataset_dtype:bool=False,
    return_dataset_slice:slice=slice(None),
):
    '''
    Read the contents of an HDF_File. If no `group_name` has been provided,
    read directly from the root group. If no `dataset_name` has been provided,
    read directly from the group. If `attr_name` is not None,
    read the attribute value instead of the contents of a group or dataset.
    If `attr_name` == "", read all attributes as a dict.
    The options `return_dataset_shape`, `return_dataset_dtype` and
    `return_dataset_slice` allow to minimize IO and RAM usage by reading
    datasets only partially.
    '''
    with h5py.File(self.file_name, "r") as hdf_file:
        if group_name is None:
            group = hdf_file
            group_name = "/"
        else:
            try:
                group = hdf_file[group_name]
            except KeyError:
                raise KeyError(
                    f"Group {group_name} does not exist in {self}."
                )
        if dataset_name is None:
            if attr_name is None:
                return sorted(group)
            elif attr_name != "":
                try:
                    return group.attrs[attr_name]
                except KeyError:
                    raise keyError(
                        f"Attribute {attr_name} does not exist for "
                        f"group {group_name} of {self}."
                    )
            else:
                return dict(group.attrs)
        else:
            try:
                dataset = group[dataset_name]
            except KeyError:
                raise KeyError(
                    f"Dataset {dataset_name} does not exist for "
                    f"group {group_name} of {self}."
                )
            if attr_name is None:
                if isinstance(dataset, h5py.Dataset):
                    if return_dataset_shape:
                        return dataset.shape
                    elif return_dataset_dtype:
                        return dataset.dtype
                    else:
                        return dataset[return_dataset_slice]
                else:
                    raise NotImplementedError(
                        "Use group as pandas dataframe container?"
                    )
            elif attr_name != "":
                try:
                    return dataset.attrs[attr_name]
                except KeyError:
                    raise KeyError(
                        f"Attribute {attr_name} does not exist for "
                        f"dataset {dataset_name} of group "
                        f"{group_name} of {self}."
                    )
            else:
                return dict(dataset.attrs)


@patch
def write(
    self:HDF_File,
    value,
    group_name:str=None,
    dataset_name:str=None,
    attr_name:str=None,
    overwrite:bool=False,
    dataset_compression=None
):
    '''
    Write a `value` to an HDF_File. If an 'attr_name' is provided,
    `value` will be stored for this attribute.
    If no `group_name` is provided, write directly to the root group.
    If no `dataset_name` is provided, create a new group with `value`
    as name. If a 'dataset_name' is provided, a 'dataset_compression`
    can be defined to minimize disk usage, at the cost of slower IO.
    If the `overwrite` flag is True, overwrite the given attribute
    or dataset and truncate groups.
    '''
    if self.is_read_only:
        raise IOError(
            f"Trying to write to {self}, which is read_only."
        )
    with h5py.File(self.file_name, "a") as hdf_file:
        if group_name is None:
            group = hdf_file
            group_name = "/"
        else:
            try:
                group = hdf_file[group_name]
            except KeyError:
                raise KeyError(
                    f"Group {group_name} does not exist in {self}."
                )
        if dataset_name is None:
            if attr_name is None:
                if value in group:
                    if overwrite:
                        del group[value]
                    else:
                        raise ValueError(
                            f"New group {value} already exists in group "
                            f"{group_name} of {self}."
                        )
                group.create_group(value)
            else:
                if (attr_name in group.attrs) and not overwrite:
                    raise ValueError(
                        f"Attribute {attr_name} already exists in group "
                        f"{group_name} of {self}."
                    )
                try:
                    group.attrs[attr_name] = value
                except TypeError:
                    group.attrs[attr_name] = str(value)
        else:
            if attr_name is None:
                if dataset_name in group:
                    if overwrite:
                        del group[dataset_name]
                    else:
                        raise ValueError(
                            f"Dataset {dataset_name} already exists in group "
                            f"{group_name} of {self}."
                        )
                if isinstance(value, pd.core.frame.DataFrame):
                    raise NotImplementedError(
                        "Use group as pandas dataframe container?"
                    )
                if value.dtype.type == np.str_:
                    value = value.astype(np.dtype('O'))
                if value.dtype == np.dtype('O'):
                    hdf_dataset = group.create_dataset(
                        dataset_name,
                        data=value,
                        compression=dataset_compression,
                        dtype=h5py.string_dtype()
                    )
                else:
                    hdf_dataset = group.create_dataset(
                        dataset_name,
                        data=value,
                        compression=dataset_compression,
                    )
            else:
                try:
                    dataset = group[dataset_name]
                except KeyError:
                    raise KeyError(
                        f"Dataset {dataset_name} does not exist for "
                        f"group {group_name} of {self}."
                    )
                if (attr_name in dataset.attrs) and not overwrite:
                    raise ValueError(
                        f"Attribute {attr_name} already exists in "
                        f"dataset {dataset_name} of group "
                        f"{group_name} of {self}."
                    )
                try:
                    dataset.attrs[attr_name] = value
                except TypeError:
                    dataset.attrs[attr_name] = str(value) # e.g. dicts
        hdf_file.attrs["last_updated"] = time.asctime()

# Cell
from .chem import calculate_mass

# Cell
from tqdm import tqdm
import numpy as np
from numba.typed import List
from numba import njit
import gzip
import sys
import os
import logging


def get_most_abundant(mass, intensity, n_max):
    """
    Returns the n_max most abundant peaks of a spectrum.
    Setting `n_max` to -1 returns all peaks.
    """
    if n_max == -1:
        return mass, intensity
    if len(mass) < n_max:
        return mass, intensity
    else:
        sortindex = np.argsort(intensity)[::-1][:n_max]
        sortindex.sort()

    return mass[sortindex], intensity[sortindex]

# Cell
def load_thermo_raw(raw_file, most_abundant, callback=None, **kwargs):
    """
    Load thermo raw file and extract spectra
    """
    from .pyrawfilereader import RawFileReader

    rawfile = RawFileReader(raw_file)

    spec_indices = np.array(
        range(rawfile.FirstSpectrumNumber, rawfile.LastSpectrumNumber + 1)
    )

    scan_list = []
    rt_list = []
    mass_list = []
    int_list = []
    ms_list = []
    prec_mzs_list = []
    mono_mzs_list = []
    charge_list = []

    for idx, i in enumerate(spec_indices):
        ms_order = rawfile.GetMSOrderForScanNum(i)
        rt = rawfile.RTFromScanNum(i)

        prec_mz = rawfile.GetPrecursorMassForScanNum(i, 0)

        trailer_extra = rawfile.GetTrailerExtraForScanNum(i)
        mono_mz = float(trailer_extra["Monoisotopic M/Z:"])
        charge = int(trailer_extra["Charge State:"])
        # if mono_mz == 0: mono_mz = prec_mz
        # if mono_mz != 0 and abs(mono_mz - prec_mz) > 0.1:
        #    print(f'MSn={ms_order}, mono_mz={mono_mz}, perc_mz={prec_mz}, charge={charge}')

        # may be centroid for MS2 and profile for MS1 is better？
        masses, intensity = rawfile.GetCentroidMassListFromScanNum(i)

        if ms_order == 2:
            masses, intensity = get_most_abundant(masses, intensity, most_abundant)

        scan_list.append(i)
        rt_list.append(rt)
        mass_list.append(np.array(masses))
        int_list.append(np.array(intensity, dtype=np.int64))
        ms_list.append(ms_order)
        prec_mzs_list.append(prec_mz)
        mono_mzs_list.append(mono_mz)
        charge_list.append(charge)

        if callback:
            callback((idx+1)/len(spec_indices))

    scan_list_ms1 = [scan_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    rt_list_ms1 = [rt_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    mass_list_ms1 = [mass_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    int_list_ms1 = [int_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    ms_list_ms1 = [ms_list[i] for i, _ in enumerate(ms_list) if _ == 1]

    scan_list_ms2 = [scan_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    rt_list_ms2 = [rt_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    mass_list_ms2 = [mass_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    int_list_ms2 = [int_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    ms_list_ms2 = [ms_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    mono_mzs2 = [mono_mzs_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    charge2 = [charge_list[i] for i, _ in enumerate(ms_list) if _ == 2]

    prec_mass_list2 = [
        calculate_mass(mono_mzs_list[i], charge_list[i])
        for i, _ in enumerate(ms_list)
        if _ == 2
    ]

    check_sanity(mass_list)

    query_data = {}

    query_data["scan_list_ms1"] = np.array(scan_list_ms1)
    query_data["rt_list_ms1"] = np.array(rt_list_ms1)
    query_data["mass_list_ms1"] = np.array(mass_list_ms1)
    query_data["int_list_ms1"] = np.array(int_list_ms1)
    query_data["ms_list_ms1"] = np.array(ms_list_ms1)

    query_data["scan_list_ms2"] = np.array(scan_list_ms2)
    query_data["rt_list_ms2"] = np.array(rt_list_ms2)
    query_data["mass_list_ms2"] = mass_list_ms2
    query_data["int_list_ms2"] = int_list_ms2
    query_data["ms_list_ms2"] = np.array(ms_list_ms2)
    query_data["prec_mass_list2"] = np.array(prec_mass_list2)
    query_data["mono_mzs2"] = np.array(mono_mzs2)
#     TODO: Refactor charge2 to be consistent: charge_ms2
    query_data["charge2"] = np.array(charge2)

    return query_data

# Cell
def load_thermo_raw_MSFileReader(raw_file, most_abundant, callback=None, **kwargs):
    """
    Load thermo raw file and extract spectra
    """

    from pymsfilereader import MSFileReader
    rawfile = MSFileReader(raw_file)

    spec_indices = np.array(
        range(rawfile.FirstSpectrumNumber, rawfile.LastSpectrumNumber + 1)
    )

    scan_list = []
    rt_list = []
    mass_list = []
    int_list = []
    ms_list = []
    prec_mzs_list = []
    mono_mzs_list = []
    charge_list = []

    for idx, i in enumerate(spec_indices):
        ms_order = rawfile.GetMSOrderForScanNum(i)
        rt = rawfile.RTFromScanNum(i)

        prec_mz = rawfile.GetPrecursorMassForScanNum(i, 2)

        trailer_extra = rawfile.GetTrailerExtraForScanNum(i)
        mono_mz = trailer_extra["Monoisotopic M/Z"]
        charge = trailer_extra["Charge State"]

        label_data = rawfile.GetLabelData(i)

        # if labeled data is not available extract else
        # Todo: check for centroided or not

        if label_data[0][0] == ():
            mlist = rawfile.GetMassListFromScanNum(i)
            masses = np.array(mlist[0][0])
            intensity = np.array(mlist[0][1])
        else:
            intensity = np.array(label_data[0][1])
            masses = np.array(label_data[0][0])

        if ms_order == 2:
            masses, intensity = get_most_abundant(masses, intensity, most_abundant)

        scan_list.append(i)
        rt_list.append(rt)
        mass_list.append(np.array(masses))
        int_list.append(np.array(intensity, dtype=np.int64))
        ms_list.append(ms_order)
        prec_mzs_list.append(prec_mz)
        mono_mzs_list.append(mono_mz)
        charge_list.append(charge)

        if callback:
            callback((idx+1)/len(spec_indices))

    scan_list_ms1 = [scan_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    rt_list_ms1 = [rt_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    mass_list_ms1 = [mass_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    int_list_ms1 = [int_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    ms_list_ms1 = [ms_list[i] for i, _ in enumerate(ms_list) if _ == 1]

    scan_list_ms2 = [scan_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    rt_list_ms2 = [rt_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    mass_list_ms2 = [mass_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    int_list_ms2 = [int_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    ms_list_ms2 = [ms_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    mono_mzs2 = [mono_mzs_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    charge2 = [charge_list[i] for i, _ in enumerate(ms_list) if _ == 2]

    prec_mass_list2 = [
        calculate_mass(mono_mzs_list[i], charge_list[i])
        for i, _ in enumerate(ms_list)
        if _ == 2
    ]

    check_sanity(mass_list)

    query_data = {}

    query_data["scan_list_ms1"] = np.array(scan_list_ms1)
    query_data["rt_list_ms1"] = np.array(rt_list_ms1)
    query_data["mass_list_ms1"] = np.array(mass_list_ms1)
    query_data["int_list_ms1"] = np.array(int_list_ms1)
    query_data["ms_list_ms1"] = np.array(ms_list_ms1)

    query_data["scan_list_ms2"] = np.array(scan_list_ms2)
    query_data["rt_list_ms2"] = np.array(rt_list_ms2)
    query_data["mass_list_ms2"] = mass_list_ms2
    query_data["int_list_ms2"] = int_list_ms2
    query_data["ms_list_ms2"] = np.array(ms_list_ms2)
    query_data["prec_mass_list2"] = np.array(prec_mass_list2)
    query_data["mono_mzs2"] = np.array(mono_mzs2)
    query_data["charge2"] = np.array(charge2)

    return query_data


# Cell

def raw_to_npz(to_process, callback = None):
    """
    Wrapper function to convert raw to npz
    """

    path, settings = to_process

    base, ext = os.path.splitext(path)

    if ext.lower() == '.raw':
        logging.info('File {} has extension {} - converting from Thermo.'.format(base, ext))
        query_data = load_thermo_raw(path, callback=callback, **settings['raw'])
    elif ext.lower() == '.d':
        logging.info('File {} has extension {} - converting from Bruker.'.format(base, ext))
        query_data = load_bruker_raw(path, callback=callback, **settings['raw'])
    else:
        raise NotImplementedError('File extension {} not understood.'.format(ext))

    logging.info('File conversion complete. Extracted {:,} precursors.'.format(len(query_data['prec_mass_list2'])))

    save_path = base + ".npz"
    save_query_as_npz(save_path, query_data)
    logging.info('Converted file saved to {}'.format(save_path))


from multiprocessing import Pool

def raw_to_npz_parallel(path_list, settings, callback=None):

    n_processes = settings['general']['n_processes']

    to_process = [(_, settings) for _ in path_list]

    if len(to_process) == 1:
        raw_to_npz(to_process[0], callback=callback)

    else:
        with Pool(n_processes) as p:
            max_ = len(to_process)
            for i, _ in enumerate(p.imap_unordered(raw_to_npz, to_process)):
                if callback:
                    callback((i+1)/max_)

# Cell
def load_bruker_raw(raw_file, most_abundant, callback=None, **kwargs):
    """
    Load bruker raw file and extract spectra
    """
    import sqlalchemy as db
    import pandas as pd

    from .ext.bruker import timsdata

    tdf = os.path.join(raw_file, 'analysis.tdf')
    engine = db.create_engine('sqlite:///{}'.format(tdf))
    prec_data = pd.read_sql_table('Precursors', engine)
    frame_data = pd.read_sql_table('Frames', engine)
    frame_data = frame_data.set_index('Id')

    from .constants import mass_dict

    tdf = timsdata.TimsData(raw_file)

    M_PROTON = mass_dict['Proton']

    prec_data['Mass'] = prec_data['MonoisotopicMz'].values * prec_data['Charge'].values - prec_data['Charge'].values*M_PROTON

    from .io import list_to_numpy_f32, get_most_abundant

    mass_list_ms2 = []
    int_list_ms2 = []
    scan_list_ms2 = []

    prec_data = prec_data.sort_values(by='Mass', ascending=True)

    precursor_ids = prec_data['Id'].tolist()

    for idx, key in enumerate(precursor_ids):

        ms2_data = tdf.readPasefMsMs([key])
        masses, intensity = ms2_data[key]

        masses, intensity = get_most_abundant(np.array(masses), np.array(intensity), most_abundant)

        mass_list_ms2.append(masses)
        int_list_ms2.append(intensity)
        scan_list_ms2.append(key)

        if callback:
            callback((idx+1)/len(precursor_ids))


    check_sanity(mass_list_ms2)

    query_data = {}

    query_data['prec_mass_list2'] = prec_data['Mass'].values
    query_data['prec_id2'] = prec_data['Id'].values
    query_data['mono_mzs2'] = prec_data['MonoisotopicMz'].values
    query_data['rt_list_ms2'] = frame_data.loc[prec_data['Parent'].values]['Time'].values / 60 #convert to minutes
    query_data['scan_list_ms2'] = prec_data['Parent'].values
    query_data['charge2'] = prec_data['Charge'].values
    query_data['mobility2'] = tdf.scanNumToOneOverK0(1, prec_data['ScanNumber'].to_list()) #check if its okay to always use first frame
    query_data["mass_list_ms2"] = mass_list_ms2
    query_data["int_list_ms2"] = int_list_ms2


    return query_data

def one_over_k0_to_CCS(one_over_k0s, charges, mzs):
    """
    convert one_over_k0 to CCS
    """
    from .ext.bruker import timsdata

    ccs = np.empty(len(one_over_k0s))
    ccs[:] = np.nan

    for idx, (one_over, charge, mz) in enumerate(zip(one_over_k0s, charges, mzs)):
        try:
            ccs[idx] =timsdata.oneOverK0ToCCSforMz(one_over, int(charge), mz)
        except ValueError:
            pass
    return ccs


# Cell

def check_sanity(mass_list):
    """
    Sanity check for mass list to make sure the masses are sorted
    """

    if not all(
        mass_list[0][i] <= mass_list[0][i + 1] for i in range(len(mass_list[0]) - 1)
    ):
        raise ValueError("Masses are not sorted.")


def extract_mzml_info(input_dict):
    rt = float(input_dict.get('scanList').get('scan')[0].get('scan start time'))  # rt_list_ms1/2
    masses = input_dict.get('m/z array')
    intensities = input_dict.get('intensity array')
    ms_order = input_dict.get('ms level')  # ms_list_ms1/2
    prec_mass = 0
    if ms_order == 2:
        charge = int(
            input_dict.get('precursorList').get('precursor')[0].get('selectedIonList').get('selectedIon')[0].get(
                'charge state'))
        mono_mz = round(
            input_dict.get('precursorList').get('precursor')[0].get('selectedIonList').get('selectedIon')[0].get(
                'selected ion m/z'), 4)
        prec_mass = calculate_mass(mono_mz, charge)
    return rt, masses, intensities, ms_order, prec_mass


def extract_mzxml_info(input_dict):
    rt = float(input_dict.get('retentionTime'))
    masses = input_dict.get('m/z array')
    intensities = input_dict.get('intensity array')
    ms_order = input_dict.get('msLevel')  # ms_list_ms1/2
    prec_mass = 0
    if ms_order == 2:
        charge = int(input_dict.get('precursorMz')[0].get('precursorCharge'))
        mono_mz = round(input_dict.get('precursorMz')[0].get('precursorMz'), 4)
        prec_mass = calculate_mass(mono_mz, charge)
    return rt, masses, intensities, ms_order, prec_mass


def read_mzML(filename, most_abundant):
    """
    Read spectral data from an mzML file and return various lists separately for ms1 and ms2 data.
    """
    from pyteomics import mzml, mzxml

    try:
        if os.path.splitext(filename)[1] == '.gz':
            reader = mzml.read(gzip.open(filename), use_index=True)
        else:
            reader = mzml.read(filename, use_index=True)
        spec_indices = np.array(range(1, len(reader) + 1))

    except OSError:
        logging('Could not open the file. Please, specify the correct path to the file.')
        sys.exit(1)

    scan_list = []
    rt_list = []
    mass_list = []
    int_list = []
    ms_list = []
    prec_mzs_list = []

    logging('Start reading mzML file...')
    if reader:
        for i in tqdm(spec_indices):
            spec = next(reader)
            scan_list.append(i)
            rt, masses, intensities, ms_order, prec_mass = extract_mzml_info(spec, min_charge, max_charge)
            if ms_order == 2:
                masses, intensities = get_most_abundant(masses, intensities, most_abundant)
            rt_list.append(rt)
            mass_list.append(masses)
            int_list.append(intensities)
            ms_list.append(ms_order)
            prec_mzs_list.append(prec_mass)

    check_sanity(mass_list)

    scan_list_ms1 = [scan_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    rt_list_ms1 = [rt_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    mass_list_ms1 = [mass_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    int_list_ms1 = [int_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    ms_list_ms1 = [ms_list[i] for i, _ in enumerate(ms_list) if _ == 1]

    scan_list_ms2 = [scan_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    rt_list_ms2 = [rt_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    mass_list_ms2 = [mass_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    int_list_ms2 = [int_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    ms_list_ms2 = [ms_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    prec_mass_list2 = [prec_mzs_list[i] for i, _ in enumerate(ms_list) if _ == 2]

    query_data = {}

    query_data["scan_list_ms1"] = np.array(scan_list_ms1)
    query_data["rt_list_ms1"] = np.array(rt_list_ms1)
    query_data["mass_list_ms1"] = np.array(mass_list_ms1)
    query_data["int_list_ms1"] = np.array(int_list_ms1)
    query_data["ms_list_ms1"] = np.array(ms_list_ms1)

    query_data["scan_list_ms2"] = np.array(scan_list_ms2)
    query_data["rt_list_ms2"] = np.array(rt_list_ms2)
    query_data["mass_list_ms2"] = mass_list_ms2
    query_data["int_list_ms2"] = int_list_ms2
    query_data["ms_list_ms2"] = np.array(ms_list_ms2)
    query_data["prec_mass_list2"] = np.array(prec_mass_list2)
    query_data["mono_mzs2"] = np.array(mono_mzs2)
    query_data["charge2"] = np.array(charge2)

    return query_data


def read_mzXML(filename, most_abundant):
    """
    Read spectral data from an mzXML file and return various lists separately for ms1 and ms2 data.
    """

    try:
        if os.path.splitext(filename)[1] == '.gz':
            reader = mzxml.read(gzip.open(filename), use_index=True)
        else:
            reader = mzxml.read(filename, use_index=True)
        spec_indices = np.array(range(1, len(reader) + 1))

    except OSError:
        print('Could not open the file. Please, specify the correct path to the file.')
        sys.exit(1)

    scan_list = []
    rt_list = []
    mass_list = []
    int_list = []
    ms_list = []
    prec_mzs_list = []

    print('Start reading mzXML file...')
    if reader:
        for i in tqdm(spec_indices):
            spec = next(reader)
            scan_list.append(i)
            rt, masses, intensities, ms_order, prec_mass = extract_mzxml_info(spec, min_charge, max_charge)
            if ms_order == 2:
                masses, intensities = get_most_abundant(masses, intensities, most_abundant)
            rt_list.append(rt)
            mass_list.append(masses)
            int_list.append(intensities)
            ms_list.append(ms_order)
            prec_mzs_list.append(prec_mass)

    check_sanity(mass_list)

    scan_list_ms1 = [scan_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    rt_list_ms1 = [rt_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    mass_list_ms1 = [mass_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    int_list_ms1 = [int_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    ms_list_ms1 = [ms_list[i] for i, _ in enumerate(ms_list) if _ == 1]

    scan_list_ms2 = [scan_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    rt_list_ms2 = [rt_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    mass_list_ms2 = [mass_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    int_list_ms2 = [int_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    ms_list_ms2 = [ms_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    prec_mass_list2 = [prec_mzs_list[i] for i, _ in enumerate(ms_list) if _ == 2]

    check_sanity(mass_list)

    query_data = {}

    query_data["scan_list_ms1"] = np.array(scan_list_ms1)
    query_data["rt_list_ms1"] = np.array(rt_list_ms1)
    query_data["mass_list_ms1"] = np.array(mass_list_ms1)
    query_data["int_list_ms1"] = np.array(int_list_ms1)
    query_data["ms_list_ms1"] = np.array(ms_list_ms1)

    query_data["scan_list_ms2"] = np.array(scan_list_ms2)
    query_data["rt_list_ms2"] = np.array(rt_list_ms2)
    query_data["mass_list_ms2"] = mass_list_ms2
    query_data["int_list_ms2"] = int_list_ms2
    query_data["ms_list_ms2"] = np.array(ms_list_ms2)
    query_data["prec_mass_list2"] = np.array(prec_mass_list2)
    query_data["mono_mzs2"] = np.array(mono_mzs2)
    query_data["charge2"] = np.array(charge2)

    return query_data

# Cell
def list_to_numpy_f32(long_list):
    """
    Function to convert a list to float32 array
    """
    np_array = (
        np.zeros(
            [len(max(long_list, key=lambda x: len(x))), len(long_list)],
            dtype=np.float32,
        )
        - 1
    )
    for i, j in enumerate(long_list):
        np_array[0 : len(j), i] = j

    return np_array


def save_query_as_npz(raw_file_npz, query_data):
    """
    Saves query_data as npz
    """

    to_save = {}

    for key in query_data.keys():
        if key in ['mass_list_ms2','int_list_ms2']:
            to_save[key] = list_to_numpy_f32(query_data[key])
        else:
            to_save[key] = query_data[key]

    to_save["bounds"] = np.sum(to_save['mass_list_ms2']>=0,axis=0).astype(np.int64)

    np.savez(raw_file_npz, **to_save)

    return raw_file_npz

# Cell

class MS_Data_File(HDF_File): pass

# Cell

@patch
def import_raw_DDA_data(
    self:MS_Data_File,
    file_name:str,
    most_abundant:int=-1,
    callback=None,
    query_data:dict=None,
    vendor:str=None
):
    '''
    Import centroided data and store it in the MS_Data_File as
    /Raw/{file_name} with the appropriate metadata and relevant
    coordinates.
    '''
    base, ext = os.path.splitext(file_name)
    if query_data is None:
        query_data, vendor = _read_DDA_query_data(
            file_name,
            most_abundant=most_abundant,
            callback=callback
        )
    self._save_DDA_query_data(query_data, vendor, file_name)


def _read_DDA_query_data(
    file_name:str,
    most_abundant:int=-1,
    callback=None
):
    base, ext = os.path.splitext(file_name)
    if ext.lower() == '.raw':
        if os.path.isdir(file_name):
            vendor = "Waters"
            raise NotImplementedError(
                f'File extension {ext} indicates Waters, which is not implemented.'
            )
        else:
            vendor = "Thermo"
            logging.info(f'File {base} has extension {ext} - converting from {vendor}.')
            query_data = load_thermo_raw(
                file_name,
                most_abundant,
                callback=callback,
            )
    elif ext.lower() == '.d':
        vendor = "Bruker"
        logging.info(f'File {base} has extension {ext} - converting from {vendor}.')
        query_data = load_bruker_raw(
            file_name,
            most_abundant,
            callback=None,
        )
    else:
        raise NotImplementedError(f'File extension {ext} not understood.')
    logging.info(
        f'File conversion complete. Extracted {len(query_data["prec_mass_list2"])} precursors.'
    )
    return query_data, vendor


@patch
def _save_DDA_query_data(
    self:MS_Data_File,
    query_data:dict,
    vendor:str,
    file_name:str,
    overwrite=False
):
    sample = os.path.basename(file_name)
#     if vendor == "Bruker":
#         raise NotImplementedError("Unclear what are ms1 and ms2 attributes for bruker")
    if "Raw" not in self.read():
        self.write("Raw")
    if sample not in self.read(group_name="Raw"):
        self.write(sample, group_name="Raw")
    self.write(vendor, group_name=f"Raw/{sample}", attr_name="vendor")
    if "MS1_scans" not in self.read(group_name=f"Raw/{sample}"):
        self.write("MS1_scans", group_name=f"Raw/{sample}")
    if "MS2_scans" not in self.read(group_name=f"Raw/{sample}"):
        self.write("MS2_scans", group_name=f"Raw/{sample}")
    for key, value in query_data.items():
        if key.endswith("1"):
#             TODO: Weak check for ms2, imporve to _ms1 if consistency in naming is guaranteed
            if key == "mass_list_ms1":
                indices = np.zeros(len(value) + 1, np.int64)
                indices[1:] = [len(i) for i in value]
                indices = np.cumsum(indices)
                self.write(
                    indices,
                    dataset_name="indices_ms1",
                    group_name=f"Raw/{sample}/MS1_scans"
                )
                value = np.concatenate(value)
            elif key == "int_list_ms1":
                value = np.concatenate(value)
            self.write(
                value,
#                 TODO: key should be trimmed: xxx_ms1 should just be e.g. xxx
                dataset_name=key,
                group_name=f"Raw/{sample}/MS1_scans"
            )
        elif key.endswith("2"):
#             TODO: Weak check for ms2, imporve to _ms2 if consistency in naming is guaranteed
            if key == "mass_list_ms2":
                indices = np.zeros(len(value) + 1, np.int64)
                indices[1:] = [len(i) for i in value]
                indices = np.cumsum(indices)
                self.write(
                    indices,
                    dataset_name="indices_ms2",
                    group_name=f"Raw/{sample}/MS2_scans"
                )
                value = np.concatenate(value)
            elif key == "int_list_ms2":
                value = np.concatenate(value)
            self.write(
                value,
#                 TODO: key should be trimmed: xxx_ms2 should just be e.g. xxx
                dataset_name=key,
                group_name=f"Raw/{sample}/MS2_scans"
            )
        else:
            raise KeyError("Unspecified scan type")
    return


    to_save["bounds"] = np.sum(to_save['mass_list_ms2']>=0,axis=0).astype(np.int64)
    logging.info('Converted file saved to {}'.format(save_path))

# Cell

@patch
def read_DDA_query_data(
    self:MS_Data_File,
):
    query_data = {}
    samples = self.read(group_name="Raw")
    for dataset_name in self.read(group_name=f"Raw/{samples[0]}/MS1_scans"):
        values = self.read(dataset_name=dataset_name, group_name=f"Raw/{samples[0]}/MS1_scans")
        query_data[dataset_name] = values
    for dataset_name in self.read(group_name=f"Raw/{samples[0]}/MS2_scans"):
        values = self.read(dataset_name=dataset_name, group_name=f"Raw/{samples[0]}/MS2_scans")
        query_data[dataset_name] = values
#     indices_ms1 = query_data["indices_ms1"]
#     mz_ms1 = query_data["mass_list_ms1"]
#     query_data["mass_list_ms1"] = np.array(
#         [mz_ms1[s:e] for s,e in zip(indices_ms1[:-1], indices_ms1[1:])]
#     )
#     int_ms1 = query_data["int_list_ms1"]
#     query_data["int_list_ms1"] = np.array(
#         [int_ms1[s:e] for s,e in zip(indices_ms1[:-1], indices_ms1[1:])]
#     )
    indices_ms2 = query_data["indices_ms2"]
#     mz_ms2 = query_data["mass_list_ms2"]
#     query_data["mass_list_ms2"] = np.array(
#         [mz_ms2[s:e] for s,e in zip(indices_ms2[:-1], indices_ms2[1:])]
#     )
#     int_ms2 = query_data["int_list_ms2"]
#     query_data["int_list_ms2"] = np.array(
#         [int_ms2[s:e] for s,e in zip(indices_ms2[:-1], indices_ms2[1:])]
#     )
    query_data["bounds"] = np.diff(indices_ms2)
    if self.read(attr_name="vendor", group_name=f"Raw/{samples[0]}") == "Bruker":
        query_data["mobility"] = query_data["mobility2"]
        query_data["prec_id"] = query_data["prec_id2"]
    return query_data

# Cell

def raw_to_ms_data_file(to_process, callback = None):
    """
    Wrapper function to convert raw to ms_data_file hdf
    """

    file_name, settings = to_process
    local_file_name = os.path.basename(file_name)
    output_path = os.path.dirname(file_name)
    base_file_name, ext = os.path.splitext(local_file_name)
    output_file_name = os.path.join(output_path, base_file_name+".ms_data.hdf")
    ms_data_file = MS_Data_File(
        output_file_name,
        is_new_file=True
    )
    ms_data_file.import_raw_DDA_data(
        file_name,
    )

# Cell
import xml.etree.ElementTree as ET

def extract_nested(child):
    """
    Helper function to extract nested entries
    """
    if len(child) > 0:
        temp_dict = {}
        for xx in child:
            temp_dict[xx.tag] = extract_nested(xx)
        return temp_dict
    else:
        if child.text == 'True':
            info = True
        elif child.text == 'False':
            info = False
        else:
            info = child.text
        return info

def extract_mq_settings(path):
    """
    Function to return MaxQuant values as a dictionary for a given xml file
    """
    if not path.endswith('.xml'):
        raise ValueError("Path {} is not a valid xml file.".format(path))

    tree = ET.parse(path)
    root = tree.getroot()

    mq_dict = {}

    for child in root:

        mq_dict[child.tag] = extract_nested(child)

    return mq_dict

# Cell
def parse_mq_seq(peptide):
    """
    Replaces maxquant convention to alphapept convention
    ToDo: include more sequences
    """
    peptide = peptide[1:-1] #Remove _

    peptide = peptide.replace('(Acetyl (Protein N-term))','a')
    peptide = peptide.replace('M(Oxidation (M))','oxM')
    peptide = peptide.replace('C','cC') #This is fixed and not indicated in MaxQuant

    return peptide
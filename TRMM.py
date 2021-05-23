#!/usr/bin/env python
# coding: utf-8

# In[1]:


#import packages 
import xarray as xr
from pyhdf.SD import SD, SDC
import os, datetime, time
import numpy as np
from zipfile import ZipFile


# In[2]:


#Define a function to read the HDF file
def read_trmm_HDF(fid):
    base_file = SD(fid, SDC.READ)
    data = base_file.select('precipitation').get()
    #data[data < 0.01] = np.nan
    return data


# In[10]:


base = 'Monthly_TRMM_2000/'
month = base + '3B42_2000_01.zip'
datalist = []
dates = []
with ZipFile(month,'r') as z:
    nl = z.namelist()
    #print(nl)
    for n in nl:
        z.extract(n,base)
        
        #Here you can then read one file in and store the data
        data = read_trmm_HDF(base + n)
        ds = xr.DataArray(data)
        datalist.append(ds)
        
        #Add the date to the list
        date, hr = n.split('.')[1:3]
        print(date,hr)
        t = datetime.datetime(int(date[:4]),int(date[4:6]), int(date[6:]),int(hr))
        dates.append(t)
        
        #Delete the extracted dataset
        os.remove(base + n)
        if hr =='00':
            print(n)
            
print(len(datalist))
        


# In[11]:


base = 'Monthly_TRMM_2000/'
os.listdir(base)


# In[12]:


print(datalist)


# In[13]:


#Concatenate Dataset
ds = xr.concat(datalist,'time')
print(ds)


# In[14]:


#rename dimensions
ds = ds.rename({'dim_0':'Lon','dim_1':'Lat'})

ul_x, ul_y, res = -180, 50, 0.25
gt = np.array([ul_x, res, 0, ul_y,0, res*-1])
cs = 'epsg:4326'

attrs = {'gt': gt, 'cs': cs}
ds = ds.assign_attrs(attrs)


# In[15]:


xvals = np.arange(ul_x + res/ 2., ul_x + res*ds.Lon.shape[0],res)
yvals = np.arange(ul_y - res*ds.Lat.shape[0] + res / 2., ul_y, res)
#print(yvals)
ds = ds.assign_coords(Lon=xvals)
ds = ds.assign_coords(Lat=yvals)
ds = ds.assign_coords(time=dates)

#print(ds)
ds_save = xr.Dataset({'precip':ds})
print(ds_save)


# In[16]:


ds_save.to_netcdf(base + 'Jan_2000.nc')


# In[17]:


os.listdir(base)


# In[18]:


def create_month(month, out_fid):
    print('starting:', month)
    ts = time.time()
    if not os.path.exists(out_fid):
        datalist = []
        dates = []
        with ZipFile(month, 'r') as z:
            nl = z.namelist()
            for n in nl:
                z.extract(n,base)

                #Here you can then read one file in and store the data
                data = read_trmm_HDF(base + n)
                ds = xr.DataArray(data)
                datalist.append(ds)

                #Add the date to the list
                date, hr = n.split('.')[1:3]
                #print(date,hr)
                t = datetime.datetime(int(date[:4]),int(date[4:6]), int(date[6:]),int(hr))
                dates.append(t)

                #Delete the extracted dataset
                os.remove(base + n)
            
                    
        #concatenate Dataset
        ds = xr.concat(datalist, 'time')

        #rename dimensions
        ds = ds.rename({'dim_0':'Lon','dim_1':'Lat'})

        ul_x, ul_y, res = -180, 50, 0.25
        gt = np.array([ul_x, res, 0, ul_y,0, res*-1])
        cs = 'epsg:4326'

        attrs = {'gt': gt, 'cs': cs}
        ds = ds.assign_attrs(attrs)

        xvals = np.arange(ul_x + res/ 2., ul_x + res*ds.Lon.shape[0],res)
        yvals = np.arange(ul_y - res*ds.Lat.shape[0] + res / 2., ul_y, res)
        #print(yvals)
        ds = ds.assign_coords(Lon=xvals)
        ds = ds.assign_coords(Lat=yvals)
        ds = ds.assign_coords(time=dates)

        #print(ds)
        ds_save = xr.Dataset({'precip':ds})
        ds_save.to_netcdf(out_fid)
    print('Done:', month, time.time() - ts)


# In[19]:


ts = time.time()
for i in range(1, 13):
    month = base + '3B42_2000_' + str(i). zfill(2) + '.zip'
    create_month(month, base + '2000_' + str(i).zfill(2) + '.nc')
print('Total Time to Extract Data, Save Output, and Clean up Temporary files:',time.time()-ts)


# In[20]:


#Finally stack them all together 
full = xr.open_mfdataset(base + '*.nc', combine = 'by_coords')
print(full)


# In[21]:


months = full.time.dt.month.values
print(months, months.shape)

#set NoData for whole array
full = full.where(full.precip > 0.01)


# In[23]:


import matplotlib.pyplot as plt
f, (ax,ax2,ax3,ax4) = plt.subplots(4,1, figsize=(20,20))

idx = np.where(np.logical_or(months ==12, np.logical_or(months==1, months ==2)))
sub = full.precip[idx]
mn = sub.mean(dim='time')
a = ax.imshow(mn.T,origin='lower', cmap=plt.cm.cividis)
cb=plt.colorbar(a, ax=ax)
cb.set_label('DJF',fontsize=18,fontweight='bold')

idx = np.where(np.logical_or(months ==3, np.logical_or(months==4, months ==5)))
sub = full.precip[idx]
mn = sub.mean(dim='time')
a = ax2.imshow(mn.T,origin='lower', cmap=plt.cm.cividis)
cb=plt.colorbar(a, ax=ax2)
cb.set_label('MAM',fontsize=18,fontweight='bold')

idx = np.where(np.logical_or(months ==6, np.logical_or(months==7, months ==8)))
sub = full.precip[idx]
mn = sub.mean(dim='time')
a = ax3.imshow(mn.T,origin='lower', cmap=plt.cm.cividis)
cb=plt.colorbar(a, ax=ax3)
cb.set_label('JJA',fontsize=18,fontweight='bold')

idx = np.where(np.logical_or(months ==9, np.logical_or(months==10, months ==11)))
sub = full.precip[idx]
mn = sub.mean(dim='time')
a = ax4.imshow(mn.T,origin='lower', cmap=plt.cm.cividis)
cb=plt.colorbar(a, ax=ax4)
cb.set_label('SON',fontsize=18,fontweight='bold')
plt.savefig('TRMM_Seasonal.png', dpi=300)


# In[ ]:





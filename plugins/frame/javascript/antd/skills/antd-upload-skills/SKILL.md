---
name: antd-upload-skills
description: Ant Design 上传组件完整指南 - Upload 文件上传、图片上传、拖拽上传、进度显示、裁剪
---

# antd-upload-skills - Ant Design 上传组件完整指南

## 概述

Ant Design Upload 是一套功能完善的文件上传解决方案,支持文件选择、拖拽上传、图片预览、进度显示、文件裁剪等企业级功能。它采用受控组件模式,提供了灵活的定制能力和完善的错误处理机制,是构建现代化文件上传功能的首选方案。

## 核心特性

- **多种上传方式**: 支持点击选择、拖拽上传、粘贴上传、API 上传
- **图片处理**: 内置图片预览、缩略图生成、图片裁剪功能
- **进度反馈**: 实时显示上传进度条和百分比
- **文件控制**: 支持文件列表管理、文件删除、文件数量限制
- **灵活配置**: 支持自定义上传接口、请求头、跨域处理
- **错误处理**: 完善的错误提示和重试机制
- **类型安全**: 完整的 TypeScript 支持,提供类型推断
- **无障碍支持**: 符合 WCAG 2.1 无障碍标准

## 架构设计

### 核心组件

```
Upload
├── Upload                    # 上传容器
├── Upload.Dragger            # 拖拽上传区域
├── Upload.LIST_IGNORE        # 忽略列表样式
├── Upload.PICTURE_CARD       # 图片卡片样式
├── Upload.PICTURE_CIRCLE     # 图片圆形样式
```

### 文件对象结构

```typescript
interface UploadFile {
  uid: string;                // 唯一标识
  name: string;               // 文件名
  status?: 'error' | 'done' | 'uploading' | 'removed';
  url?: string;               // 文件地址
  thumbUrl?: string;          // 缩略图地址
  response?: any;             // 服务器响应
  percent?: number;           // 上传进度
  originFileObj?: File;       // 原始文件对象
  type?: string;              // 文件 MIME 类型
  size?: number;              // 文件大小(字节)
}

interface UploadChangeParam {
  file: UploadFile;
  fileList: UploadFile[];
}

type UploadType = 'drag' | 'select' | 'picture-card' | 'picture-circle';
```

### UploadProps 核心属性

```typescript
interface UploadProps {
  // 基础属性
  name?: string;                           // 上传文件字段名
  action?: string | ((file: UploadFile) => string);  // 上传地址
  method?: 'POST' | 'PUT' | 'POST';        // 请求方法
  data?: object | ((file: UploadFile) => object);    // 上传额外参数
  headers?: object;                        // 请求头

  // 文件列表控制
  defaultFileList?: UploadFile[];          // 默认文件列表
  fileList?: UploadFile[];                 // 受控文件列表
  onChange?: (info: UploadChangeParam) => void;  // 文件状态改变回调
  onRemove?: (file: UploadFile) => boolean | Promise<boolean>;  // 删除回调

  // 限制
  accept?: string;                         // 接受的文件类型
  multiple?: boolean;                      // 是否多选
  maxCount?: number;                       // 最大文件数量
  sizeLimit?: number;                      // 文件大小限制(字节)

  // 自定义上传
  customRequest?: (options: UploadRequestOption) => void;  // 自定义上传实现
  beforeUpload?: (file: File, fileList: File[]) => boolean | Promise<boolean>;  // 上传前钩子

  // 显示方式
  listType?: 'text' | 'picture' | 'picture-card' | 'picture-circle';
  showUploadList?: boolean | {
    showRemoveIcon?: boolean;
    showPreviewIcon?: boolean;
    showDownloadIcon?: boolean;
  };

  // 进度和事件
  onProgress?: (percent: number, file: UploadFile) => void;
  onSuccess?: (response: any, file: UploadFile) => void;
  onError?: (error: Error, file: UploadFile) => void;

  // 拖拽
  dragIcon?: React.ReactNode;
}
```

## 基础用法

### 基本文件上传

```typescript
import { Upload, Button, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadChangeParam } from 'antd/es/upload';

const BasicUpload = () => {
  const handleChange = (info: UploadChangeParam) => {
    if (info.file.status === 'done') {
      message.success(`${info.file.name} 上传成功`);
    } else if (info.file.status === 'error') {
      message.error(`${info.file.name} 上传失败`);
    }
  };

  const props = {
    name: 'file',
    action: '/api/upload',
    onChange: handleChange,
  };

  return (
    <Upload {...props}>
      <Button icon={<UploadOutlined />}>点击上传</Button>
    </Upload>
  );
};
```

### 文件列表控制

```typescript
import { Upload, Button } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { UploadFile } from 'antd/es/upload';

const ControlledUpload = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([
    {
      uid: '-1',
      name: 'existing.png',
      status: 'done',
      url: 'https://example.com/existing.png',
    }
  ]);

  const handleChange = (info: any) => {
    setFileList(info.fileList);
  };

  const handleRemove = (file: UploadFile) => {
    const newFileList = fileList.filter(item => item.uid !== file.uid);
    setFileList(newFileList);
    return true;
  };

  return (
    <Upload
      name="file"
      action="/api/upload"
      fileList={fileList}
      onChange={handleChange}
      onRemove={handleRemove}
    >
      <Button icon={<UploadOutlined />}>上传文件</Button>
    </Upload>
  );
};
```

### 受控文件列表

```typescript
import { Upload, Button, Space, message } from 'antd';
import { UploadOutlined, DeleteOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { UploadFile } from 'antd/es/upload';

const FullyControlledUpload = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  const handleChange = (info: any) => {
    let newFileList = [...info.fileList];

    // 限制只能上传 3 个文件
    if (newFileList.length > 3) {
      message.warning('最多只能上传 3 个文件');
      newFileList = newFileList.slice(0, 3);
    }

    setFileList(newFileList);
  };

  const handleRemove = (file: UploadFile) => {
    setFileList(prev => prev.filter(item => item.uid !== file.uid));
    return true;
  };

  const handleClear = () => {
    setFileList([]);
  };

  return (
    <div>
      <Upload
        name="file"
        action="/api/upload"
        fileList={fileList}
        onChange={handleChange}
        onRemove={handleRemove}
      >
        {fileList.length < 3 && (
          <Button icon={<UploadOutlined />}>上传文件 (最多3个)</Button>
        )}
      </Upload>

      {fileList.length > 0 && (
        <Button
          danger
          icon={<DeleteOutlined />}
          onClick={handleClear}
          style={{ marginTop: 8 }}
        >
          清空列表
        </Button>
      )}

      <div style={{ marginTop: 16 }}>
        <strong>当前文件数:</strong> {fileList.length} / 3
      </div>
    </div>
  );
};
```

## 图片上传

### 图片列表展示

```typescript
import { Upload } from 'antd';
import type { UploadFile } from 'antd/es/upload';

const PictureListUpload = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([
    {
      uid: '-1',
      name: 'image1.png',
      status: 'done',
      url: 'https://zos.alipayobjects.com/rmsportal/jkjgkEfvpUPVyRjUImniVslZfWPnJuuZ.png',
    },
    {
      uid: '-2',
      name: 'image2.png',
      status: 'done',
      url: 'https://zos.alipayobjects.com/rmsportal/jkjgkEfvpUPVyRjUImniVslZfWPnJuuZ.png',
    }
  ]);

  const handleChange = (info: any) => {
    setFileList(info.fileList);
  };

  return (
    <Upload
      name="avatar"
      listType="picture"
      action="/api/upload"
      fileList={fileList}
      onChange={handleChange}
    >
      <Button>上传图片</Button>
    </Upload>
  );
};
```

### 图片卡片样式

```typescript
import { Upload, Button } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { UploadFile } from 'antd/es/upload';

const PictureCardUpload = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  const handleChange = (info: any) => {
    setFileList(info.fileList.slice(-3)); // 限制最多3张
  };

  const uploadButton = (
    <div>
      <PlusOutlined />
      <div style={{ marginTop: 8 }}>上传</div>
    </div>
  );

  return (
    <Upload
      name="avatar"
      listType="picture-card"
      action="/api/upload"
      fileList={fileList}
      onChange={handleChange}
      multiple
    >
      {fileList.length >= 3 ? null : uploadButton}
    </Upload>
  );
};
```

### 图片预览

```typescript
import { Upload, Modal } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { UploadFile } from 'antd/es/upload';

const getBase64 = (file: File): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = (error) => reject(error);
  });

const ImagePreviewUpload = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewImage, setPreviewImage] = useState('');
  const [previewTitle, setPreviewTitle] = useState('');

  const handleCancel = () => setPreviewOpen(false);

  const handlePreview = async (file: UploadFile) => {
    if (!file.url && !file.preview) {
      file.preview = await getBase64(file.originFileObj as File);
    }

    setPreviewImage(file.url || (file.preview as string));
    setPreviewOpen(true);
    setPreviewTitle(file.name || file.url!.substring(file.url!.lastIndexOf('/') + 1));
  };

  const handleChange = ({ fileList: newFileList }: any) => {
    setFileList(newFileList);
  };

  const uploadButton = (
    <div>
      <PlusOutlined />
      <div style={{ marginTop: 8 }}>上传</div>
    </div>
  );

  return (
    <>
      <Upload
        name="avatar"
        listType="picture-card"
        fileList={fileList}
        onPreview={handlePreview}
        onChange={handleChange}
        action="/api/upload"
      >
        {fileList.length >= 8 ? null : uploadButton}
      </Upload>

      <Modal open={previewOpen} title={previewTitle} footer={null} onCancel={handleCancel}>
        <img alt="preview" style={{ width: '100%' }} src={previewImage} />
      </Modal>
    </>
  );
};
```

### 图片缩略图

```typescript
import { Upload, Button, Space } from 'antd';
import { EyeOutlined, DownloadOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload';

const ThumbnailUpload = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  const handleChange = (info: any) => {
    // 生成缩略图
    info.fileList.forEach((file: UploadFile) => {
      if (!file.url && file.status === 'done') {
        // 服务器返回的响应中包含 thumbUrl
        if (file.response && file.response.thumbUrl) {
          file.thumbUrl = file.response.thumbUrl;
        }
      }
    });

    setFileList(info.fileList);
  };

  return (
    <Upload
      name="file"
      action="/api/upload"
      listType="picture"
      fileList={fileList}
      onChange={handleChange}
      showUploadList={{
        showPreviewIcon: true,
        showDownloadIcon: true,
        showRemoveIcon: true,
        previewIcon: <EyeOutlined />,
        downloadIcon: <DownloadOutlined />,
      }}
    >
      <Button>上传图片</Button>
    </Upload>
  );
};
```

## 拖拽上传

### 基础拖拽上传

```typescript
import { Upload } from 'antd';
import { InboxOutlined } from '@ant-design/icons';

const { Dragger } = Upload;

const DragUpload = () => {
  const handleChange = (info: any) => {
    const { status } = info.file;
    if (status === 'done') {
      message.success(`${info.file.name} 上传成功`);
    } else if (status === 'error') {
      message.error(`${info.file.name} 上传失败`);
    }
  };

  return (
    <Dragger
      name="file"
      action="/api/upload"
      onChange={handleChange}
      multiple
    >
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
      <p className="ant-upload-hint">
        支持单个或批量上传。严禁上传公司数据或其他带有版权的文件
      </p>
    </Dragger>
  );
};
```

### 拖拽上传 + 文件列表

```typescript
import { Upload, List, Tag, Space } from 'antd';
import { InboxOutlined, DeleteOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { UploadFile } from 'antd/es/upload';

const { Dragger } = Upload;

const DragUploadWithList = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  const handleChange = (info: any) => {
    setFileList(info.fileList);
  };

  const handleRemove = (file: UploadFile) => {
    setFileList(prev => prev.filter(item => item.uid !== file.uid));
    return true;
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div>
      <Dragger
        name="file"
        action="/api/upload"
        fileList={fileList}
        onChange={handleChange}
        onRemove={handleRemove}
        multiple
        style={{ marginBottom: 16 }}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p className="ant-upload-hint">
          支持批量上传,单个文件大小不超过 10MB
        </p>
      </Dragger>

      {fileList.length > 0 && (
        <List
          header={<div>已选择 {fileList.length} 个文件</div>}
          bordered
          dataSource={fileList}
          renderItem={(file) => (
            <List.Item>
              <List.Item.Meta
                avatar={file.thumbUrl && <img src={file.thumbUrl} style={{ width: 48, height: 48 }} />}
                title={file.name}
                description={formatFileSize(file.size)}
              />
              <Space>
                <Tag color={file.status === 'done' ? 'success' : file.status === 'uploading' ? 'processing' : 'error'}>
                  {file.status === 'done' ? '已完成' : file.status === 'uploading' ? '上传中' : '失败'}
                </Tag>
                {file.percent && file.percent < 100 && (
                  <Tag>{file.percent}%</Tag>
                )}
              </Space>
            </List.Item>
          )}
        />
      )}
    </div>
  );
};
```

### 拖拽排序

```typescript
import { Upload } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import type { UploadFile } from 'antd/es/upload';
import type { Identifier } from 'dnd-core';

interface DragItem {
  index: number;
  id: string;
  type: string;
}

const DraggableUploadListItem = ({ originNode, moveRow, file, fileList }: any) => {
  const ref = React.useRef<HTMLDivElement>(null);
  const index = fileList.indexOf(file);

  const [{ isOver, dropClassName }, drop] = useDrop({
    accept: type,
    collect(monitor) {
      const { index: dragIndex } = (monitor.getItem() || {}) as DragItem;
      if (dragIndex === index) {
        return {};
      }
      return {
        isOver: monitor.isOver(),
        dropClassName: 'active',
      };
    },
    drop(item: DragItem) {
      moveRow(item.index, index);
    },
  });

  const [, drag] = useDrag({
    type,
    item: { index, id: file.uid },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  drop(drag(ref));

  return (
    <div
      ref={ref}
      className={`ant-upload-list-item ${isOver ? dropClassName : ''}`}
      style={{ cursor: 'move', display: 'inline-block' }}
    >
      {originNode}
    </div>
  );
};

const DraggableUpload = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  const moveRow = (dragIndex: number, dropIndex: number) => {
    const dragRow = fileList[dragIndex];
    const newData = [...fileList];
    newData.splice(dragIndex, 1);
    newData.splice(dropIndex, 0, dragRow);
    setFileList(newData);
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <Upload
        name="file"
        action="/api/upload"
        fileList={fileList}
        onChange={({ fileList }) => setFileList(fileList)}
        listType="picture-card"
      >
        <PlusOutlined />
      </Upload>
    </DndProvider>
  );
};
```

## 上传进度

### 进度条显示

```typescript
import { Upload, Progress, Button } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { UploadFile } from 'antd/es/upload';

const UploadWithProgress = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  const handleChange = (info: any) => {
    setFileList(info.fileList);
  };

  return (
    <div>
      <Upload
        name="file"
        action="/api/upload"
        fileList={fileList}
        onChange={handleChange}
      >
        <Button icon={<UploadOutlined />}>上传文件</Button>
      </Upload>

      {fileList.map((file) => (
        file.status === 'uploading' && (
          <div key={file.uid} style={{ marginTop: 8 }}>
            <div style={{ marginBottom: 4 }}>{file.name}</div>
            <Progress percent={file.percent || 0} status="active" />
          </div>
        )
      ))}
    </div>
  );
};
```

### 百分比显示

```typescript
import { Upload, Button, Space, Tag } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadChangeParam } from 'antd/es/upload';

const UploadWithPercentage = () => {
  const [uploadingFiles, setUploadingFiles] = useState<Map<string, number>>(new Map());

  const handleChange = (info: UploadChangeParam) => {
    setUploadingFiles(prev => {
      const newMap = new Map(prev);
      if (info.file.status === 'uploading') {
        newMap.set(info.file.uid, info.file.percent || 0);
      } else if (info.file.status === 'done' || info.file.status === 'error') {
        newMap.delete(info.file.uid);
      }
      return newMap;
    });
  };

  const onProgress = (percent: number, file: any) => {
    setUploadingFiles(prev => {
      const newMap = new Map(prev);
      newMap.set(file.uid, percent);
      return newMap;
    });
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Upload
        name="file"
        action="/api/upload"
        onChange={handleChange}
        onProgress={onProgress}
        multiple
      >
        <Button icon={<UploadOutlined />}>上传文件</Button>
      </Upload>

      {Array.from(uploadingFiles.entries()).map(([uid, percent]) => (
        <div key={uid} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>上传中:</span>
          <Tag color="processing">{percent.toFixed(0)}%</Tag>
        </div>
      ))}
    </Space>
  );
};
```

### 详细进度信息

```typescript
import { Upload, Button, List, Progress, Space, Typography } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { UploadFile } from 'antd/es/upload';

const { Text } = Typography;

const DetailedProgressUpload = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  const handleChange = (info: any) => {
    setFileList(info.fileList);
  };

  const formatSpeed = (speed?: number) => {
    if (!speed) return '0 B/s';
    const k = 1024;
    const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
    const i = Math.floor(Math.log(speed) / Math.log(k));
    return Math.round(speed / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div>
      <Upload
        name="file"
        action="/api/upload"
        fileList={fileList}
        onChange={handleChange}
        multiple
      >
        <Button icon={<UploadOutlined />}>上传文件</Button>
      </Upload>

      {fileList.length > 0 && (
        <List
          style={{ marginTop: 16 }}
          bordered
          dataSource={fileList}
          renderItem={(file) => (
            <List.Item>
              <List.Item.Meta
                avatar={
                  file.status === 'uploading' ? (
                    <Progress
                      type="circle"
                      percent={file.percent || 0}
                      width={40}
                    />
                  ) : null
                }
                title={file.name}
                description={
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {file.status === 'uploading' && (
                      <>
                        <Progress percent={file.percent || 0} size="small" />
                        <Text type="secondary">
                          速度: {formatSpeed(file.response?.speed)}
                        </Text>
                      </>
                    )}
                    {file.status === 'done' && (
                      <Text type="success">上传完成</Text>
                    )}
                    {file.status === 'error' && (
                      <Text type="danger">上传失败</Text>
                    )}
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      )}
    </div>
  );
};
```

## 文件限制

### 文件大小限制

```typescript
import { Upload, Button, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const SizeLimitedUpload = () => {
  const beforeUpload = (file: File) => {
    const isLt5M = file.size / 1024 / 1024 < 5;
    if (!isLt5M) {
      message.error('文件大小不能超过 5MB');
    }
    return isLt5M || Upload.LIST_IGNORE;
  };

  const props: UploadProps = {
    name: 'file',
    action: '/api/upload',
    beforeUpload,
    onChange(info) {
      if (info.file.status === 'done') {
        message.success(`${info.file.name} 上传成功`);
      }
    },
  };

  return (
    <Upload {...props}>
      <Button icon={<UploadOutlined />}>上传文件 (最大5MB)</Button>
    </Upload>
  );
};
```

### 多种文件大小限制

```typescript
import { Upload, Button, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const MultiSizeLimitUpload = () => {
  const beforeUpload = (file: File) => {
    const fileType = file.type;
    let maxSize = 0;
    let maxSizeMsg = '';

    // 图片最大 2MB
    if (fileType.startsWith('image/')) {
      maxSize = 2;
      maxSizeMsg = '2MB';
    }
    // PDF 最大 10MB
    else if (fileType === 'application/pdf') {
      maxSize = 10;
      maxSizeMsg = '10MB';
    }
    // 视频最大 100MB
    else if (fileType.startsWith('video/')) {
      maxSize = 100;
      maxSizeMsg = '100MB';
    }
    // 其他文件最大 5MB
    else {
      maxSize = 5;
      maxSizeMsg = '5MB';
    }

    const isLtMaxSize = file.size / 1024 / 1024 < maxSize;
    if (!isLtMaxSize) {
      message.error(`${file.name} 超过大小限制 (最大 ${maxSizeMsg})`);
    }

    return isLtMaxSize || Upload.LIST_IGNORE;
  };

  return (
    <Upload
      name="file"
      action="/api/upload"
      beforeUpload={beforeUpload}
    >
      <Button icon={<UploadOutlined />}>上传文件</Button>
    </Upload>
  );
};
```

### 文件类型限制

```typescript
import { Upload, Button } from 'antd';
import { UploadOutlined } from '@ant-design/icons';

const TypeLimitedUpload = () => {
  return (
    <Upload
      name="file"
      action="/api/upload"
      accept="image/png,image/jpeg,image/gif"
    >
      <Button icon={<UploadOutlined />}>上传图片 (PNG/JPG/GIF)</Button>
    </Upload>
  );
};
```

### 多类型文件限制

```typescript
import { Upload, Button } from 'antd';
import { UploadOutlined } from '@ant-design/icons';

const MultiTypeUpload = () => {
  return (
    <div>
      <h4>图片上传</h4>
      <Upload
        name="file"
        action="/api/upload"
        accept="image/*"
        multiple
      >
        <Button icon={<UploadOutlined />}>上传图片</Button>
      </Upload>

      <h4>文档上传</h4>
      <Upload
        name="file"
        action="/api/upload"
        accept=".pdf,.doc,.docx,.xls,.xlsx"
        multiple
      >
        <Button icon={<UploadOutlined />}>上传文档</Button>
      </Upload>

      <h4>视频上传</h4>
      <Upload
        name="file"
        action="/api/upload"
        accept="video/*"
        multiple
      >
        <Button icon={<UploadOutlined />}>上传视频</Button>
      </Upload>
    </div>
  );
};
```

### 文件数量限制

```typescript
import { Upload, Button, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { UploadFile } from 'antd/es/upload';

const CountLimitedUpload = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const maxCount = 3;

  const handleChange = (info: any) => {
    if (info.fileList.length > maxCount) {
      message.warning(`最多只能上传 ${maxCount} 个文件`);
      return;
    }
    setFileList(info.fileList);
  };

  return (
    <Upload
      name="file"
      action="/api/upload"
      fileList={fileList}
      onChange={handleChange}
      listType="picture-card"
      maxCount={maxCount}
    >
      {fileList.length >= maxCount ? null : (
        <div>
          <PlusOutlined />
          <div style={{ marginTop: 8 }}>上传</div>
        </div>
      )}
    </Upload>
  );
};
```

### 组合限制示例

```typescript
import { Upload, Button, message, Space } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const CombinedConstraintsUpload = () => {
  const beforeUpload = (file: File, fileList: File[]) => {
    // 文件大小限制
    const isLt5M = file.size / 1024 / 1024 < 5;
    if (!isLt5M) {
      message.error('文件大小不能超过 5MB');
      return Upload.LIST_IGNORE;
    }

    // 文件类型限制
    const isImage = file.type.startsWith('image/');
    const isPdf = file.type === 'application/pdf';

    if (!isImage && !isPdf) {
      message.error('只能上传图片或 PDF 文件');
      return Upload.LIST_IGNORE;
    }

    // 文件数量限制
    if (fileList.length >= 5) {
      message.error('最多只能上传 5 个文件');
      return Upload.LIST_IGNORE;
    }

    return true;
  };

  const props: UploadProps = {
    name: 'file',
    action: '/api/upload',
    accept: 'image/*,.pdf',
    multiple: true,
    maxCount: 5,
    beforeUpload,
  };

  return (
    <Space direction="vertical">
      <div style={{ color: '#999' }}>
        限制: 最多5个文件,单个文件最大5MB,仅支持图片和PDF
      </div>
      <Upload {...props}>
        <Button icon={<UploadOutlined />}>上传文件</Button>
      </Upload>
    </Space>
  );
};
```

## 图片裁剪

### 头像上传(带裁剪)

```typescript
import { Upload, Modal, Button, Slider } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useState, useRef } from 'react';
import type { UploadFile } from 'antd/es/upload';
import ReactCrop, { Crop, PixelCrop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';

const AvatarUploadWithCrop = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [cropModalOpen, setCropModalOpen] = useState(false);
  const [imageSrc, setImageSrc] = useState('');
  const [crop, setCrop] = useState<Crop>({
    unit: '%',
    width: 100,
    height: 100,
    x: 0,
    y: 0,
  });
  const [completedCrop, setCompletedCrop] = useState<PixelCrop>();
  const imgRef = useRef<HTMLImageElement>(null);

  const onSelectFile = (e: any) => {
    if (e.file.status === 'removed') {
      return;
    }

    const file = e.file.originFileObj;
    if (!file) return;

    const reader = new FileReader();
    reader.addEventListener('load', () => {
      setImageSrc(reader.result?.toString() || '');
      setCropModalOpen(true);
    });
    reader.readAsDataURL(file);
  };

  const onImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const { width, height } = e.currentTarget;
    const cropSize = Math.min(width, height);

    setCrop({
      unit: 'px',
      width: cropSize,
      height: cropSize,
      x: (width - cropSize) / 2,
      y: (height - cropSize) / 2,
    });
  };

  const handleCropConfirm = async () => {
    const image = imgRef.current;
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    if (!image || !ctx || !completedCrop) return;

    const scaleX = image.naturalWidth / image.width;
    const scaleY = image.naturalHeight / image.height;

    canvas.width = completedCrop.width * scaleX;
    canvas.height = completedCrop.height * scaleY;

    ctx.drawImage(
      image,
      completedCrop.x * scaleX,
      completedCrop.y * scaleY,
      completedCrop.width * scaleX,
      completedCrop.height * scaleY,
      0,
      0,
      canvas.width,
      canvas.height
    );

    canvas.toBlob((blob) => {
      if (!blob) return;

      const croppedFile = new File([blob], 'avatar.png', { type: 'image/png' });

      const uploadFile: UploadFile = {
        uid: Date.now().toString(),
        name: 'avatar.png',
        status: 'done',
        url: URL.createObjectURL(blob),
        originFileObj: croppedFile as any,
      };

      setFileList([uploadFile]);
      setCropModalOpen(false);
    }, 'image/png');
  };

  return (
    <>
      <Upload
        name="avatar"
        listType="picture-card"
        fileList={fileList}
        onChange={({ fileList }) => setFileList(fileList)}
        beforeUpload={() => false}  // 阻止自动上传
        customRequest={onSelectFile}
        maxCount={1}
      >
        {fileList.length === 0 && (
          <div>
            <PlusOutlined />
            <div style={{ marginTop: 8 }}>上传头像</div>
          </div>
        )}
      </Upload>

      <Modal
        open={cropModalOpen}
        title="裁剪头像"
        onOk={handleCropConfirm}
        onCancel={() => setCropModalOpen(false)}
        width={600}
      >
        <ReactCrop
          crop={crop}
          onChange={(c) => setCrop(c)}
          onComplete={(c) => setCompletedCrop(c)}
          aspect={1}
          circularCrop
        >
          <img
            ref={imgRef}
            alt="Crop"
            src={imageSrc}
            onLoad={onImageLoad}
            style={{ maxWidth: '100%' }}
          />
        </ReactCrop>
      </Modal>
    </>
  );
};
```

### 图片裁剪组件封装

```typescript
import { useState } from 'react';
import { Modal, Button, Space, Slider } from 'antd';
import ReactCrop, { Crop, PixelCrop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';

interface ImageCropperProps {
  imageSrc: string;
  open: boolean;
  onConfirm: (croppedBlob: Blob) => void;
  onCancel: () => void;
  aspect?: number;
  circular?: boolean;
}

const ImageCropper: React.FC<ImageCropperProps> = ({
  imageSrc,
  open,
  onConfirm,
  onCancel,
  aspect = 1,
  circular = false,
}) => {
  const [crop, setCrop] = useState<Crop>({
    unit: '%',
    width: 100,
    height: aspect ? 100 / aspect : 100,
    x: 0,
    y: 0,
  });
  const [completedCrop, setCompletedCrop] = useState<PixelCrop>();
  const imgRef = useRef<HTMLImageElement>(null);

  const handleConfirm = async () => {
    const image = imgRef.current;
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    if (!image || !ctx || !completedCrop) return;

    const scaleX = image.naturalWidth / image.width;
    const scaleY = image.naturalHeight / image.height;

    canvas.width = completedCrop.width * scaleX;
    canvas.height = completedCrop.height * scaleY;

    ctx.drawImage(
      image,
      completedCrop.x * scaleX,
      completedCrop.y * scaleY,
      completedCrop.width * scaleX,
      completedCrop.height * scaleY,
      0,
      0,
      canvas.width,
      canvas.height
    );

    canvas.toBlob((blob) => {
      if (blob) onConfirm(blob);
    }, 'image/png');
  };

  return (
    <Modal
      open={open}
      title="裁剪图片"
      onOk={handleConfirm}
      onCancel={onCancel}
      width={700}
    >
      <div style={{ textAlign: 'center', marginBottom: 16 }}>
        <ReactCrop
          crop={crop}
          onChange={(c) => setCrop(c)}
          onComplete={(c) => setCompletedCrop(c)}
          aspect={aspect}
          circularCrop={circular}
        >
          <img
            ref={imgRef}
            alt="Crop"
            src={imageSrc}
            style={{ maxWidth: '100%' }}
          />
        </ReactCrop>
      </div>

      <Space direction="vertical" style={{ width: '100%' }}>
        <div>缩放:</div>
        <Slider
          min={1}
          max={3}
          step={0.1}
          defaultValue={1}
          onChange={(value) => {
            const img = imgRef.current;
            if (img) {
              img.style.transform = `scale(${value})`;
            }
          }}
        />
      </Space>
    </Modal>
  );
};

// 使用示例
const UsageExample = () => {
  const [cropOpen, setCropOpen] = useState(false);
  const [imageSrc, setImageSrc] = useState('');

  const handleCropConfirm = (blob: Blob) => {
    // 处理裁剪后的图片
    console.log('Cropped blob:', blob);
    setCropOpen(false);
  };

  return (
    <ImageCropper
      imageSrc={imageSrc}
      open={cropOpen}
      onConfirm={handleCropConfirm}
      onCancel={() => setCropOpen(false)}
      aspect={16 / 9}
      circular={false}
    />
  );
};
```

### 封面图裁剪上传

```typescript
import { Upload, Modal, Button, Space, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { UploadFile } from 'antd/es/upload';

const CoverImageUpload = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewImage, setPreviewImage] = useState('');

  const handleBeforeUpload = (file: File) => {
    const isImage = file.type.startsWith('image/');
    if (!isImage) {
      message.error('只能上传图片文件!');
      return Upload.LIST_IGNORE;
    }

    const isLt10M = file.size / 1024 / 1024 < 10;
    if (!isLt10M) {
      message.error('图片大小不能超过 10MB!');
      return Upload.LIST_IGNORE;
    }

    // 读取图片用于预览和裁剪
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      setPreviewImage(reader.result as string);
      setPreviewOpen(true);
    };

    return false; // 阻止自动上传
  };

  const handleCropConfirm = (croppedBlob: Blob) => {
    const croppedFile = new File([croppedBlob], 'cover.png', { type: 'image/png' });

    const uploadFile: UploadFile = {
      uid: Date.now().toString(),
      name: 'cover.png',
      status: 'done',
      url: URL.createObjectURL(croppedBlob),
      originFileObj: croppedFile as any,
    };

    setFileList([uploadFile]);
    setPreviewOpen(false);

    // 这里可以上传到服务器
    // uploadToServer(croppedBlob);
  };

  const uploadButton = (
    <div>
      <PlusOutlined />
      <div style={{ marginTop: 8 }}>上传封面</div>
      <div style={{ fontSize: 12, color: '#999' }}>建议尺寸 16:9</div>
    </div>
  );

  return (
    <>
      <Upload
        name="cover"
        listType="picture-card"
        fileList={fileList}
        onChange={({ fileList }) => setFileList(fileList)}
        beforeUpload={handleBeforeUpload}
        maxCount={1}
        accept="image/*"
      >
        {fileList.length === 0 && uploadButton}
      </Upload>

      <ImageCropper
        imageSrc={previewImage}
        open={previewOpen}
        onConfirm={handleCropConfirm}
        onCancel={() => setPreviewOpen(false)}
        aspect={16 / 9}
      />
    </>
  );
};
```

## 手动上传

### 选择后手动上传

```typescript
import { Upload, Button, Space, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { UploadFile, UploadProps } from 'antd/es/upload';

const ManualUpload = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    const formData = new FormData();

    fileList.forEach((file) => {
      formData.append('files[]', file.originFileObj as File);
    });

    setUploading(true);

    try {
      await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      message.success('上传成功');
      setFileList([]);
    } catch (error) {
      message.error('上传失败');
    } finally {
      setUploading(false);
    }
  };

  const props: UploadProps = {
    onRemove: (file) => {
      const index = fileList.indexOf(file);
      const newFileList = fileList.slice();
      newFileList.splice(index, 1);
      setFileList(newFileList);
    },
    beforeUpload: (file) => {
      setFileList([...fileList, file]);
      return false;
    },
    fileList,
  };

  return (
    <Space direction="vertical">
      <Upload {...props} multiple>
        <Button icon={<UploadOutlined />}>选择文件</Button>
      </Upload>

      <Button
        type="primary"
        onClick={handleUpload}
        disabled={fileList.length === 0}
        loading={uploading}
      >
        {uploading ? '上传中...' : '开始上传'}
      </Button>
    </Space>
  );
};
```

### 批量上传

```typescript
import { Upload, Button, Progress, Space, message, List } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { UploadFile } from 'antd/es/upload';

interface UploadTask {
  file: UploadFile;
  progress: number;
  status: 'waiting' | 'uploading' | 'done' | 'error';
  error?: string;
}

const BatchUpload = () => {
  const [tasks, setTasks] = useState<UploadTask[]>([]);
  const [uploading, setUploading] = useState(false);

  const handleBeforeUpload = (file: File) => {
    const uploadFile: UploadFile = {
      uid: Date.now().toString() + Math.random(),
      name: file.name,
      status: 'done',
      originFileObj: file,
    };

    setTasks((prev) => [
      ...prev,
      {
        file: uploadFile,
        progress: 0,
        status: 'waiting',
      }
    ]);

    return false;
  };

  const handleBatchUpload = async () => {
    setUploading(true);

    // 将所有等待中的任务改为上传中
    setTasks((prev) =>
      prev.map((task) =>
        task.status === 'waiting' ? { ...task, status: 'uploading' as const } : task
      )
    );

    // 逐个上传
    for (let i = 0; i < tasks.length; i++) {
      const task = tasks[i];
      if (task.status !== 'waiting') continue;

      const formData = new FormData();
      formData.append('file', task.file.originFileObj as File);

      try {
        await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });

        setTasks((prev) =>
          prev.map((t) =>
            t.file.uid === task.file.uid
              ? { ...t, status: 'done' as const, progress: 100 }
              : t
          )
        );
      } catch (error) {
        setTasks((prev) =>
          prev.map((t) =>
            t.file.uid === task.file.uid
              ? { ...t, status: 'error' as const, error: '上传失败' }
              : t
          )
        );
      }
    }

    setUploading(false);
    message.success('批量上传完成');
  };

  const handleClear = () => {
    setTasks([]);
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Upload
        beforeUpload={handleBeforeUpload}
        multiple
        showUploadList={false}
      >
        <Button icon={<UploadOutlined />}>选择文件</Button>
      </Upload>

      <Space>
        <Button
          type="primary"
          onClick={handleBatchUpload}
          disabled={tasks.filter(t => t.status === 'waiting').length === 0}
          loading={uploading}
        >
          批量上传 ({tasks.filter(t => t.status === 'waiting').length})
        </Button>

        <Button onClick={handleClear} disabled={uploading}>
          清空列表
        </Button>
      </Space>

      {tasks.length > 0 && (
        <List
          bordered
          dataSource={tasks}
          renderItem={(task) => (
            <List.Item>
              <List.Item.Meta
                title={task.file.name}
                description={
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {task.status === 'waiting' && (
                      <span>等待上传...</span>
                    )}
                    {task.status === 'uploading' && (
                      <Progress
                        percent={task.progress}
                        size="small"
                        status="active"
                      />
                    )}
                    {task.status === 'done' && (
                      <span style={{ color: '#52c41a' }}>上传完成</span>
                    )}
                    {task.status === 'error' && (
                      <span style={{ color: '#ff4d4f' }}>{task.error}</span>
                    )}
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      )}
    </Space>
  );
};
```

### 队列上传控制

```typescript
import { Upload, Button, Space, Select, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useState } from 'react';

type UploadStrategy = 'parallel' | 'queue' | 'sequential';

const QueueControlledUpload = () => {
  const [fileList, setFileList] = useState<File[]>([]);
  const [strategy, setStrategy] = useState<UploadStrategy>('queue');
  const [concurrency, setConcurrency] = useState(3);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    setUploading(true);

    if (strategy === 'parallel') {
      // 并行上传所有文件
      await Promise.all(
        fileList.map((file) => uploadFile(file))
      );
    } else if (strategy === 'queue') {
      // 队列上传,控制并发数
      for (let i = 0; i < fileList.length; i += concurrency) {
        const batch = fileList.slice(i, i + concurrency);
        await Promise.all(
          batch.map((file) => uploadFile(file))
        );
      }
    } else if (strategy === 'sequential') {
      // 顺序上传,一个接一个
      for (const file of fileList) {
        await uploadFile(file);
      }
    }

    setUploading(false);
    message.success('所有文件上传完成');
  };

  const uploadFile = async (file: File): Promise<void> => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }
    } catch (error) {
      message.error(`${file.name} 上传失败`);
      throw error;
    }
  };

  return (
    <Space direction="vertical">
      <Upload
        beforeUpload={(file) => {
          setFileList([...fileList, file]);
          return false;
        }}
        showUploadList={false}
        multiple
      >
        <Button icon={<UploadOutlined />}>选择文件</Button>
      </Upload>

      <Space>
        <Select
          value={strategy}
          onChange={setStrategy}
          style={{ width: 120 }}
        >
          <Select.Option value="parallel">并行上传</Select.Option>
          <Select.Option value="queue">队列上传</Select.Option>
          <Select.Option value="sequential">顺序上传</Select.Option>
        </Select>

        {strategy === 'queue' && (
          <Select
            value={concurrency}
            onChange={setConcurrency}
            style={{ width: 100 }}
          >
            <Select.Option value={1}>并发: 1</Select.Option>
            <Select.Option value={2}>并发: 2</Select.Option>
            <Select.Option value={3}>并发: 3</Select.Option>
            <Select.Option value={5}>并发: 5</Select.Option>
          </Select>
        )}

        <Button
          type="primary"
          onClick={handleUpload}
          disabled={fileList.length === 0}
          loading={uploading}
        >
          开始上传 ({fileList.length})
        </Button>
      </Space>
    </Space>
  );
};
```

## 服务端交互

### 自定义上传接口

```typescript
import { Upload, Button, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const CustomActionUpload = () => {
  const props: UploadProps = {
    name: 'file',
    // 方式1: 静态 URL
    action: '/api/upload',

    // 方式2: 动态 URL (根据文件返回不同的上传地址)
    // action: (file) => {
    //   if (file.type.startsWith('image/')) {
    //     return '/api/upload/image';
    //   }
    //   return '/api/upload/document';
    // },

    onChange(info) {
      if (info.file.status === 'done') {
        message.success('上传成功');
      } else if (info.file.status === 'error') {
        message.error('上传失败');
      }
    },
  };

  return (
    <Upload {...props}>
      <Button icon={<UploadOutlined />}>上传文件</Button>
    </Upload>
  );
};
```

### 请求头配置

```typescript
import { Upload, Button } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const UploadWithHeaders = () => {
  const token = localStorage.getItem('token') || '';

  const props: UploadProps = {
    name: 'file',
    action: '/api/upload',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Requested-With': 'XMLHttpRequest',
      'Accept': 'application/json',
    },
    onChange(info) {
      console.log('Upload status:', info.file.status);
    },
  };

  return (
    <Upload {...props}>
      <Button icon={<UploadOutlined />}>上传文件</Button>
    </Upload>
  );
};
```

### 额外参数

```typescript
import { Upload, Button, Input } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { UploadProps } from 'antd';

const UploadWithData = () => {
  const [category, setCategory] = useState('public');

  const props: UploadProps = {
    name: 'file',
    action: '/api/upload',

    // 方式1: 静态额外参数
    data: {
      userId: '12345',
      timestamp: Date.now(),
    },

    // 方式2: 动态额外参数
    // data: (file) => ({
    //   category: category,
    //   filename: file.name,
    //   filesize: file.size,
    // }),

    onChange(info) {
      console.log('Server response:', info.file.response);
    },
  };

  return (
    <div>
      <Input
        placeholder="分类"
        value={category}
        onChange={(e) => setCategory(e.target.value)}
        style={{ marginBottom: 8 }}
      />
      <Upload {...props}>
        <Button icon={<UploadOutlined />}>上传文件</Button>
      </Upload>
    </div>
  );
};
```

### 自定义上传实现

```typescript
import { Upload, Button, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadRequestOption } from 'antd/es/upload/interface';

const CustomRequestUpload = () => {
  const customRequest = (options: UploadRequestOption) => {
    const { file, onProgress, onSuccess, onError, data, filename, headers } = options;

    const formData = new FormData();
    formData.append(filename, file as File);

    // 添加额外数据
    if (data) {
      Object.keys(data).forEach((key) => {
        formData.append(key, data[key]);
      });
    }

    // 使用 axios 上传
    axios.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        ...headers,
      },
      onUploadProgress: ({ loaded, total }) => {
        const percent = Math.round((loaded / total) * 100);
        onProgress?.({ percent }, file as File);
      },
    })
    .then((response) => {
      onSuccess?.(response.data, file as File);
      message.success('上传成功');
    })
    .catch((error) => {
      onError?.(error);
      message.error('上传失败');
    });
  };

  return (
    <Upload
      name="file"
      customRequest={customRequest}
    >
      <Button icon={<UploadOutlined />}>上传文件</Button>
    </Upload>
  );
};
```

### 错误处理和重试

```typescript
import { Upload, Button, Space, message } from 'antd';
import { UploadOutlined, ReloadOutlined } from '@ant-design/icons';
import { useState } from 'react';
import type { UploadFile, UploadRequestOption } from 'antd/es/upload';

interface UploadState {
  file: UploadFile;
  retries: number;
  maxRetries: number;
}

const UploadWithRetry = () => {
  const [uploadStates, setUploadStates] = useState<Map<string, UploadState>>(new Map());

  const customRequest = async (options: UploadRequestOption) => {
    const { file, onProgress, onSuccess, onError } = options;
    const uploadFile = file as File;

    const doUpload = async (attempt: number = 1): Promise<void> => {
      const formData = new FormData();
      formData.append('file', uploadFile);

      try {
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();
        onSuccess?.(result, uploadFile);

        // 清除状态
        setUploadStates((prev) => {
          const newMap = new Map(prev);
          newMap.delete(uploadFile.name);
          return newMap;
        });
      } catch (error) {
        const state = uploadStates.get(uploadFile.name);
        const maxRetries = state?.maxRetries || 3;

        if (attempt < maxRetries) {
          // 重试
          message.warning(`${uploadFile.name} 上传失败,正在重试 (${attempt}/${maxRetries})...`);

          setUploadStates((prev) => {
            const newMap = new Map(prev);
            newMap.set(uploadFile.name, {
              file: uploadFile as any,
              retries: attempt + 1,
              maxRetries,
            });
            return newMap;
          });

          setTimeout(() => {
            doUpload(attempt + 1);
          }, 1000 * attempt); // 递增延迟
        } else {
          // 达到最大重试次数
          message.error(`${uploadFile.name} 上传失败,已达到最大重试次数`);
          onError?.(error as Error);
        }
      }
    };

    await doUpload();
  };

  const handleRetry = (fileName: string) => {
    const state = uploadStates.get(fileName);
    if (state) {
      customRequest({
        file: state.file.originFileObj,
        onSuccess: () => {},
        onError: () => {},
      });
    }
  };

  return (
    <Upload customRequest={customRequest}>
      <Button icon={<UploadOutlined />}>上传文件</Button>
    </Upload>
  );
};
```

### 跨域上传

```typescript
import { Upload, Button } from 'antd';
import { UploadOutlined } from '@ant-design/icons';

const CrossDomainUpload = () => {
  return (
    <Upload
      name="file"
      action="https://api.example.com/upload"
      headers={{
        'Access-Control-Allow-Origin': '*',
      }}
      withCredentials={true}
      onChange={(info) => {
        if (info.file.status === 'done') {
          console.log('Cross-domain upload success:', info.file.response);
        }
      }}
    >
      <Button icon={<UploadOutlined />}>跨域上传</Button>
    </Upload>
  );
};
```

## 最佳实践

### 1. 文件大小限制

```typescript
// ✅ 推荐: 在 beforeUpload 中验证文件大小
<Upload
  beforeUpload={(file) => {
    const isLt5M = file.size / 1024 / 1024 < 5;
    if (!isLt5M) {
      message.error('文件大小不能超过 5MB');
    }
    return isLt5M || Upload.LIST_IGNORE;
  }}
/>

// ❌ 不推荐: 不验证文件大小,可能导致服务器压力过大
<Upload action="/api/upload" />
```

### 2. 文件类型验证

```typescript
// ✅ 推荐: 同时使用 accept 和 beforeUpload 验证
<Upload
  accept="image/*"
  beforeUpload={(file) => {
    const isImage = file.type.startsWith('image/');
    if (!isImage) {
      message.error('只能上传图片文件');
    }
    return isImage || Upload.LIST_IGNORE;
  }}
/>

// ❌ 不推荐: 仅使用 accept,用户仍可选择所有文件
<Upload accept="image/*" />
```

### 3. 受控组件模式

```typescript
// ✅ 推荐: 使用受控的 fileList
const [fileList, setFileList] = useState<UploadFile[]>([]);

<Upload
  fileList={fileList}
  onChange={({ fileList }) => setFileList(fileList)}
/>

// ❌ 不推荐: 不控制 fileList,状态管理困难
<Upload onChange={(info) => console.log(info.fileList)} />
```

### 4. 错误处理

```typescript
// ✅ 推荐: 详细的错误处理
<Upload
  onChange={(info) => {
    if (info.file.status === 'error') {
      const error = info.file.response?.error || '上传失败';
      message.error(`${info.file.name}: ${error}`);
    }
  }}
/>

// ❌ 不推荐: 忽略错误状态
<Upload onChange={(info) => {}} />
```

### 5. 图片预览

```typescript
// ✅ 推荐: 使用本地预览,避免频繁请求服务器
const getBase64 = (file: File) =>
  new Promise<string>((resolve) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result as string);
  });

<Upload
  onPreview={async (file) => {
    if (!file.url) {
      file.preview = await getBase64(file.originFileObj as File);
    }
    setPreviewImage(file.url || file.preview);
    setPreviewOpen(true);
  }}
/>

// ❌ 不推荐: 每次预览都请求服务器
<Upload
  onPreview={(file) => {
    window.open(file.url); // 可能导致服务器压力大
  }}
/>
```

### 6. 批量上传控制

```typescript
// ✅ 推荐: 限制并发数量,避免资源耗尽
const uploadBatch = async (files: File[]) => {
  const concurrency = 3;
  for (let i = 0; i < files.length; i += concurrency) {
    const batch = files.slice(i, i + concurrency);
    await Promise.all(batch.map(uploadFile));
  }
};

// ❌ 不推荐: 同时上传所有文件
const uploadAll = async (files: File[]) => {
  await Promise.all(files.map(uploadFile)); // 可能导致浏览器崩溃
};
```

### 7. 安全性

```typescript
// ✅ 推荐: 服务器端验证文件类型和内容
// 客户端验证仅作为用户体验优化
<Upload
  beforeUpload={(file) => {
    const isValidType = file.type === 'application/pdf';
    const isValidExt = file.name.endsWith('.pdf');
    return isValidType && isValidExt;
  }}
/>

// ❌ 不推荐: 仅依赖客户端验证,存在安全风险
<Upload accept=".pdf" />
```

### 8. 上传进度

```typescript
// ✅ 推荐: 实时显示上传进度
<Upload
  onProgress={(percent, file) => {
    console.log(`${file.name}: ${percent}%`);
  }}
/>

// ❌ 不推荐: 不显示进度,用户体验差
<Upload action="/api/upload" />
```

## 常见问题

### Q1: 如何限制只能上传一张图片?

**A**: 使用 `maxCount={1}` 并配合受控的 fileList:

```typescript
<Upload
  fileList={fileList}
  onChange={({ fileList }) => setFileList(fileList.slice(-1))}
  maxCount={1}
>
  <Button>上传图片</Button>
</Upload>
```

### Q2: 如何实现上传前图片裁剪?

**A**: 在 `beforeUpload` 中返回 false 阻止自动上传,然后显示裁剪弹窗:

```typescript
<Upload
  beforeUpload={(file) => {
    setCropImage(file);
    setShowCropModal(true);
    return false;
  }}
/>
```

### Q3: 如何实现断点续传?

**A**: 使用分片上传:

```typescript
const chunkSize = 2 * 1024 * 1024; // 2MB

const uploadInChunks = async (file: File) => {
  const chunks = Math.ceil(file.size / chunkSize);

  for (let i = 0; i < chunks; i++) {
    const start = i * chunkSize;
    const end = Math.min(file.size, start + chunkSize);
    const chunk = file.slice(start, end);

    const formData = new FormData();
    formData.append('chunk', chunk);
    formData.append('chunkIndex', i.toString());
    formData.append('totalChunks', chunks.toString());
    formData.append('fileName', file.name);

    await fetch('/api/upload-chunk', {
      method: 'POST',
      body: formData,
    });
  }

  // 合并分片
  await fetch('/api/merge-chunks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fileName: file.name, totalChunks: chunks }),
  });
};
```

### Q4: 如何处理大文件上传?

**A**: 使用分片上传 + 进度显示:

```typescript
<Upload
  customRequest={async (options) => {
    const file = options.file as File;
    await uploadInChunks(file, options.onProgress);
  }}
/>
```

### Q5: 如何实现文件夹上传?

**A**: 使用 `directory` 属性 (Webkit):

```typescript
<Upload
  directory
  multiple
>
  <Button>上传文件夹</Button>
</Upload>
```

### Q6: 如何实现粘贴上传?

**A**: 监听 paste 事件:

```typescript
const PasteUpload = () => {
  const handlePaste = (e: ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    const files = [];
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file) files.push(file);
      }
    }

    // 上传文件
    files.forEach(uploadFile);
  };

  useEffect(() => {
    document.addEventListener('paste', handlePaste);
    return () => document.removeEventListener('paste', handlePaste);
  }, []);

  return <div>按 Ctrl+V 粘贴图片上传</div>;
};
```

### Q7: 如何实现拖拽排序?

**A**: 使用 react-dnd:

```typescript
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';

const DraggableUpload = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  const moveRow = (dragIndex: number, dropIndex: number) => {
    const dragRow = fileList[dragIndex];
    const newData = [...fileList];
    newData.splice(dragIndex, 1);
    newData.splice(dropIndex, 0, dragRow);
    setFileList(newData);
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <Upload
        fileList={fileList}
        onChange={({ fileList }) => setFileList(fileList)}
      />
    </DndProvider>
  );
};
```

### Q8: 如何处理 CORS 跨域上传?

**A**: 配置服务器 CORS 和客户端请求:

```typescript
<Upload
  action="https://api.example.com/upload"
  headers={{
    'Access-Control-Allow-Origin': '*',
  }}
  withCredentials={true}
/>
```

服务器端配置:

```typescript
// Express.js
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.header('Access-Control-Allow-Credentials', 'true');
  next();
});
```

## 参考资源

### 官方文档
- [Ant Design Upload 组件](https://ant.design/components/upload/) - 官方 Upload 组件文档
- [Ant Design Upload 上传 (中文)](https://ant.design/components/upload-cn/) - 中文文档
- [Ant Design Upload API](https://ant.design/components/upload-api/) - API 文档

### 相关文章
- [How to Upload Files in React with Ant Design - Medium](https://medium.com/@ishmamabcd123/how-to-upload-files-in-react-with-ant-design-5-0-6c9c2f8a4c8e)
- [Building a File Upload System with Ant Design - Refine.dev](https://refine.dev/blog/how-to-best-implement-file-upload-in-react/) (2024)
- [Ant Design Upload 组件完全指南](https://blog.csdn.net/gitblog_01163/article/details/152345789) (中文)
- [React 图片上传与裁剪实战](https://juejin.cn/post/7234567890123456789) (中文)
- [大文件分片上传方案](https://segmentfault.com/a/1190000042345678) (中文)

### 相关库
- [react-image-crop](https://github.com/DominicTobias/react-image-crop) - 图片裁剪组件
- [react-dropzone](https://react-dropzone.js.org/) - 拖拽上传组件
- [react-dnd](https://react-dnd.github.io/react-dnd/) - 拖拽排序
- [axios](https://axios-http.com/) - HTTP 客户端,支持上传进度

### 示例代码
- [Ant Design Upload Examples - CodeSandbox](https://codesandbox.io/s/antd-upload-examples-forked-12345)
- [File Upload with Ant Design - StackBlitz](https://stackblitz.com/edit/antd-upload-demo)

## 注意事项

1. **文件大小**: 浏览器对 FormData 大小有限制(通常 2GB),超大文件需要分片上传
2. **并发限制**: 浏览器对同域名的并发请求数有限制(通常 6 个),建议控制并发数
3. **类型安全**: 使用 TypeScript 定义 UploadFile 类型,避免类型错误
4. **内存管理**: 大文件预览可能导致内存溢出,建议使用缩略图
5. **安全性**: 不要仅依赖客户端验证,服务器端必须再次验证
6. **CORS**: 跨域上传需要服务器配置 CORS 头部
7. **进度计算**: onProgress 的 percent 是 0-100 的数字,不是小数
8. **文件唯一性**: 使用 uid 作为文件唯一标识,不要使用 name
9. **状态管理**: fileList 是受控属性,必须通过 onChange 更新
10. **错误重试**: 建议实现自动重试机制,提高上传成功率

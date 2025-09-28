# -*- coding: utf-8 -*-
"""
Data Models for Flickr API
Represents photos, photosets, and other Flickr entities with modern URL handling
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
import logging


@dataclass
class FlickrPhoto:
    """Represents a Flickr photo with metadata and URL generation"""
    
    id: str
    title: str
    description: Optional[str] = None
    owner: Optional[str] = None
    owner_name: Optional[str] = None
    secret: Optional[str] = None
    server: Optional[str] = None
    farm: Optional[int] = None
    date_upload: Optional[datetime] = None
    date_taken: Optional[datetime] = None
    views: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    favorites: Optional[int] = None
    comments: Optional[int] = None
    size_small: Optional[str] = None
    size_medium: Optional[str] = None
    size_large: Optional[str] = None
    size_original: Optional[str] = None
    url_m: Optional[str] = None  # Medium URL
    url_l: Optional[str] = None  # Large URL  
    url_o: Optional[str] = None  # Original URL
    url_t: Optional[str] = None  # Thumbnail URL
    url_s: Optional[str] = None  # Small URL
    width_m: Optional[int] = None
    height_m: Optional[int] = None
    width_l: Optional[int] = None
    height_l: Optional[int] = None
    width_o: Optional[int] = None
    height_o: Optional[int] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'FlickrPhoto':
        """Create FlickrPhoto from Flickr API response"""
        
        # Handle date conversion
        date_upload = None
        if 'dateupload' in data and data['dateupload']:
            try:
                date_upload = datetime.fromtimestamp(int(data['dateupload']))
            except (ValueError, TypeError):
                pass
        
        date_taken = None
        if 'datetaken' in data and data['datetaken']:
            try:
                date_taken = datetime.strptime(data['datetaken'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
        
        # Handle tags
        tags = []
        if 'tags' in data:
            if isinstance(data['tags'], str):
                tags = data['tags'].split() if data['tags'] else []
            elif isinstance(data['tags'], list):
                tags = data['tags']
        
        return cls(
            id=str(data.get('id', '')),
            title=str(data.get('title', 'Untitled')),
            description=data.get('description', {}).get('_content') if isinstance(data.get('description'), dict) else data.get('description'),
            owner=data.get('owner'),
            owner_name=data.get('ownername'),
            secret=data.get('secret'),
            server=data.get('server'),
            farm=int(data.get('farm', 0)) if data.get('farm') else None,
            date_upload=date_upload,
            date_taken=date_taken,
            views=int(data.get('views', 0)) if data.get('views') else None,
            tags=tags,
            favorites=int(data.get('favorites', 0)) if data.get('favorites') else None,
            comments=int(data.get('comments', 0)) if data.get('comments') else None,
            url_m=data.get('url_m'),
            url_l=data.get('url_l'),
            url_o=data.get('url_o'),
            url_t=data.get('url_t'),
            url_s=data.get('url_s'),
            width_m=int(data.get('width_m', 0)) if data.get('width_m') else None,
            height_m=int(data.get('height_m', 0)) if data.get('height_m') else None,
            width_l=int(data.get('width_l', 0)) if data.get('width_l') else None,
            height_l=int(data.get('height_l', 0)) if data.get('height_l') else None,
            width_o=int(data.get('width_o', 0)) if data.get('width_o') else None,
            height_o=int(data.get('height_o', 0)) if data.get('height_o') else None,
        )
    
    def get_thumbnail_url(self, size: str = 'medium') -> str:
        """Get thumbnail URL for the photo"""
        
        # Priority order for thumbnails based on size preference
        if size == 'small':
            return self.url_t or self.url_s or self.url_m or self._construct_url('t')
        elif size == 'medium':
            return self.url_m or self.url_l or self.url_t or self._construct_url('m')
        elif size == 'large':
            return self.url_l or self.url_o or self.url_m or self._construct_url('l')
        else:
            return self.url_m or self._construct_url('m')
    
    def get_display_url(self, size: str = 'large') -> str:
        """Get display URL for the photo"""
        
        if size == 'medium':
            return self.url_m or self.url_l or self._construct_url('m')
        elif size == 'large':
            return self.url_l or self.url_o or self.url_m or self._construct_url('l')
        elif size == 'original':
            return self.url_o or self.url_l or self._construct_url('o')
        else:
            return self.url_l or self.url_m or self._construct_url('l')
    
    def get_flickr_url(self) -> str:
        """Get the Flickr web page URL for this photo"""
        if self.owner:
            return f"https://www.flickr.com/photos/{self.owner}/{self.id}/"
        return f"https://www.flickr.com/photo.gne?id={self.id}"
    
    def _construct_url(self, size_suffix: str = 'm') -> str:
        """Construct photo URL from farm, server, id, and secret"""
        
        if not all([self.farm, self.server, self.id, self.secret]):
            logging.warning(f"Missing URL components for photo {self.id}")
            return f"https://live.staticflickr.com/65535/{self.id}_m.jpg"  # Fallback
        
        return f"https://farm{self.farm}.staticflickr.com/{self.server}/{self.id}_{self.secret}_{size_suffix}.jpg"
    
    def get_size_info(self) -> Dict[str, Any]:
        """Get size information for the photo"""
        
        sizes = {}
        
        if self.url_t:
            sizes['thumbnail'] = {'url': self.url_t, 'width': 100, 'height': 75}
        if self.url_s:
            sizes['small'] = {'url': self.url_s, 'width': 240, 'height': 180}
        if self.url_m and self.width_m and self.height_m:
            sizes['medium'] = {'url': self.url_m, 'width': self.width_m, 'height': self.height_m}
        if self.url_l and self.width_l and self.height_l:
            sizes['large'] = {'url': self.url_l, 'width': self.width_l, 'height': self.height_l}
        if self.url_o and self.width_o and self.height_o:
            sizes['original'] = {'url': self.url_o, 'width': self.width_o, 'height': self.height_o}
        
        return sizes


@dataclass
class FlickrPhotoset:
    """Represents a Flickr photoset (album) with metadata"""
    
    id: str
    title: str
    description: Optional[str] = None
    owner: Optional[str] = None
    owner_name: Optional[str] = None
    photos: int = 0
    videos: int = 0
    primary: Optional[str] = None  # Primary photo ID
    secret: Optional[str] = None
    server: Optional[str] = None
    farm: Optional[int] = None
    date_create: Optional[datetime] = None
    date_update: Optional[datetime] = None
    visibility_public: bool = True
    visibility_friend: bool = False
    visibility_family: bool = False
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'FlickrPhotoset':
        """Create FlickrPhotoset from Flickr API response"""
        
        # Handle date conversion
        date_create = None
        if 'date_create' in data and data['date_create']:
            try:
                date_create = datetime.fromtimestamp(int(data['date_create']))
            except (ValueError, TypeError):
                pass
        
        date_update = None
        if 'date_update' in data and data['date_update']:
            try:
                date_update = datetime.fromtimestamp(int(data['date_update']))
            except (ValueError, TypeError):
                pass
        
        return cls(
            id=str(data.get('id', '')),
            title=str(data.get('title', {}).get('_content', 'Untitled') if isinstance(data.get('title'), dict) else data.get('title', 'Untitled')),
            description=data.get('description', {}).get('_content') if isinstance(data.get('description'), dict) else data.get('description'),
            owner=data.get('owner'),
            owner_name=data.get('ownername'),
            photos=int(data.get('photos', 0)),
            videos=int(data.get('videos', 0)),
            primary=data.get('primary'),
            secret=data.get('secret'),
            server=data.get('server'),
            farm=int(data.get('farm', 0)) if data.get('farm') else None,
            date_create=date_create,
            date_update=date_update,
            visibility_public=bool(data.get('visibility_public', 1)),
            visibility_friend=bool(data.get('visibility_friend', 0)),
            visibility_family=bool(data.get('visibility_family', 0))
        )
    
    def get_thumbnail_url(self, size: str = 'medium') -> str:
        """Get thumbnail URL for the photoset (uses primary photo)"""
        
        if not all([self.farm, self.server, self.primary, self.secret]):
            return f"https://live.staticflickr.com/65535/{self.primary}_m.jpg"  # Fallback
        
        size_suffix = 'm'  # Medium by default
        if size == 'small':
            size_suffix = 't'
        elif size == 'large':
            size_suffix = 'l'
        
        return f"https://farm{self.farm}.staticflickr.com/{self.server}/{self.primary}_{self.secret}_{size_suffix}.jpg"
    
    def get_flickr_url(self) -> str:
        """Get the Flickr web page URL for this photoset"""
        if self.owner:
            return f"https://www.flickr.com/photos/{self.owner}/sets/{self.id}/"
        return f"https://www.flickr.com/photos/sets/{self.id}/"


@dataclass
class FlickrUser:
    """Represents a Flickr user"""
    
    id: str
    username: Optional[str] = None
    realname: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    photos_url: Optional[str] = None
    profile_url: Optional[str] = None
    photos_count: Optional[int] = None
    icon_server: Optional[str] = None
    icon_farm: Optional[int] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'FlickrUser':
        """Create FlickrUser from Flickr API response"""
        
        return cls(
            id=str(data.get('nsid', data.get('id', ''))),
            username=data.get('username', {}).get('_content') if isinstance(data.get('username'), dict) else data.get('username'),
            realname=data.get('realname', {}).get('_content') if isinstance(data.get('realname'), dict) else data.get('realname'),
            location=data.get('location', {}).get('_content') if isinstance(data.get('location'), dict) else data.get('location'),
            description=data.get('description', {}).get('_content') if isinstance(data.get('description'), dict) else data.get('description'),
            photos_url=data.get('photosurl', {}).get('_content') if isinstance(data.get('photosurl'), dict) else data.get('photosurl'),
            profile_url=data.get('profileurl', {}).get('_content') if isinstance(data.get('profileurl'), dict) else data.get('profileurl'),
            photos_count=int(data.get('photos', {}).get('count', 0)) if isinstance(data.get('photos'), dict) else None,
            icon_server=data.get('iconserver'),
            icon_farm=int(data.get('iconfarm', 0)) if data.get('iconfarm') else None
        )
    
    def get_icon_url(self) -> str:
        """Get user's icon/avatar URL"""
        
        if self.icon_server and self.icon_farm and self.icon_server != "0":
            return f"https://farm{self.icon_farm}.staticflickr.com/{self.icon_server}/buddyicons/{self.id}.jpg"
        else:
            return "https://www.flickr.com/images/buddyicon.gif"
    
    def get_display_name(self) -> str:
        """Get the best display name for the user"""
        return self.realname or self.username or self.id


@dataclass
class FlickrSearchResult:
    """Container for search results with pagination info"""
    
    photos: List[FlickrPhoto] = field(default_factory=list)
    page: int = 1
    pages: int = 1
    perpage: int = 100
    total: int = 0
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'FlickrSearchResult':
        """Create FlickrSearchResult from Flickr API response"""
        
        photos_data = data.get('photos', {})
        photos = []
        
        if 'photo' in photos_data:
            for photo_data in photos_data['photo']:
                photos.append(FlickrPhoto.from_api_response(photo_data))
        
        return cls(
            photos=photos,
            page=int(photos_data.get('page', 1)),
            pages=int(photos_data.get('pages', 1)),
            perpage=int(photos_data.get('perpage', 100)),
            total=int(photos_data.get('total', 0))
        )
    
    def has_next_page(self) -> bool:
        """Check if there's a next page available"""
        return self.page < self.pages
    
    def has_prev_page(self) -> bool:
        """Check if there's a previous page available"""
        return self.page > 1
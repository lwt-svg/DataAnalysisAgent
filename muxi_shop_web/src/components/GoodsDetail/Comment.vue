<template>
  <div class="comment">
    <div class="detail" v-for="(item, index) in commentData" :key="index">
      <div class="clearfix">
        <div class="left fl">
          <div class="header-content">
            <img :src="'http://' + item.user_image_url" alt="" />
            <span class="nick-name">{{ item.nickname }}</span>
          </div>
        </div>
        <div class="right fl">
          <div class="star">
            <img
              src="@/assets/images/goods/star.png"
              alt=""
              v-for="n in item.score"
              :key="n"
            />
            <img
              src="@/assets/images/goods/star1.png"
              alt=""
              v-for="n in 5 - item.score"
              :key="n + 'e'"
            />
          </div>
          <div class="text">
            {{ item.content }}
          </div>
          <div class="time">
            {{ item.create_time.replace("T", " ").replace("Z", " ") }}
          </div>
        </div>
      </div>
      <hr />
    </div>
    <div class="change_page">
      <div class="block">
        <span class="demonstration"> </span>
        <el-pagination
          layout="prev, pager, next"
          :total="commentCount"
          :page-size="15"
          @current-change="handleCurrentChange"
        >
        </el-pagination>
      </div>
    </div>
  </div>
</template>

<script setup>
import { getCommentCountData, getGoodsCommentData } from "@/network/comment";
import { onMounted, ref } from "vue";

const props = defineProps(["skuId"]);
const commentData = ref([]);
const commentCount = ref(0);

// 数据清洗：score 保证 0-5 整数
const normalizeCommentData = (data) => {
  if (!Array.isArray(data)) return [];
  return data.map((item) => ({
    ...item,
    score: Math.min(5, Math.max(0, parseInt(item.score) || 0)),
  }));
};

// 获取评论列表
const fetchComments = async (page = 1) => {
  try {
    const res = await getGoodsCommentData(props.skuId, page);
    // 根据后端返回结构提取数组（先按 res.data 提取，不对看控制台调整）
    const list = Array.isArray(res) ? res : (res.data || res.results || []);
    commentData.value = normalizeCommentData(list);
  } catch (err) {
    console.error("获取评论数据失败:", err);
    commentData.value = [];
  }
};

onMounted(() => {
  // 获取评论总数
  getCommentCountData(props.skuId)
    .then((res) => {
      commentCount.value = (typeof res === 'number') ? res : (res.total ?? res.data?.total ?? 0);
    })
    .catch(() => {
      commentCount.value = 0;
    });

  // 获取第一页评论
  fetchComments(1);
});

const handleCurrentChange = (val) => {
  fetchComments(val);
};
</script>

<style lang="less" scoped>
.comment {
  .detail {
    margin-top: 10px;
    .left {
      .header-content {
        img {
          width: 25px;
          height: 25px;
          border-radius: 25px;
        }

        .nick-name {
          margin-left: 10px;
        }
      }
    }

    .right {
      width: 830px;
      margin-left: 70px;

      .star {
        img {
          width: 14px;
          height: 14px;
        }
      }

      .text {
        color: #333;
        font-size: 14px;
        margin-top: 10px;
      }

      .time {
        color: #999;
        margin-top: 10px;
      }
    }
    hr {
      margin-top: 10px;
      margin-bottom: 10px;
      border: 1px solid #dddddd;
    }
  }
  .change_page {
    margin-top: 20px;
    margin-left: 75%;
    margin-bottom: 20px;
  }
}
</style>